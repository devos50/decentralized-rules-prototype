import random

import networkx as nx

from core.content import Content
from core.rule import Rule
from core.user import User, UserType


class Experiment:

    def __init__(self, settings):
        self.settings = settings
        self.rules = []
        self.content = []
        self.users = []

    def get_user_by_id(self, user_id):
        for user in self.users:
            if user.identifier == user_id:
                return user
        return None

    def create_rules(self):
        for rule_ind in range(1, self.settings.num_rules + 1):
            rule = Rule(rule_ind, "Tag %d" % rule_ind)
            rule.determine_applicable_content(self.settings.num_content_items)
            self.rules.append(rule)

    def create_content(self):
        for content_ind in range(self.settings.num_content_items):
            self.content.append("%d" % content_ind)

    def create_users(self):
        for user_ind in range(1, self.settings.num_honest_users + 1):
            user = User("%d" % user_ind)
            for content_item in self.content:
                user.content_db.add_content(Content(content_item))
            self.users.append(user)

        # Create adversarial users
        for user_ind in range(len(self.users) + 1, len(self.users) + self.settings.num_adversarial_users + 1):
            user = User("%d" % user_ind, user_type=UserType.RANDOM_VOTES)
            for content_item in self.content:  # Adversarial users have all content.
                user.content_db.add_content(Content(content_item))
            self.users.append(user)

        # Distribute rules over users
        for user in self.users:
            user_rules = [rule.get_copy() for rule in self.rules]
            user.rules_db.add_rules(user_rules)
            user.apply_rules_to_content()

    def create_votes(self):
        # Create some votes
        for user in self.users:
            for content_item in user.content_db.get_all_content():
                for tag in content_item.tags:
                    vote = True
                    if user.type == UserType.RANDOM_VOTES:
                        vote = bool(random.randint(0, 1))
                    user.vote(tag, vote)

    def connect_users(self):
        # Create a strongly connected graph
        for user_a in self.users:
            for user_b in self.users:
                if user_a == user_b:
                    continue
                user_a.connect(user_b)

    def write_correlation_graph(self):
        # Create correlation graph
        G = nx.DiGraph()
        for user in self.users:
            if not G.has_node(user.identifier):
                G.add_node(user.identifier, type=user.type, color="red" if user.type != UserType.HONEST else "black")

            if user.type != UserType.HONEST:
                continue  # We don't care about the outgoing trust edges of adversaries

            for user_ids, correlation in user.trust_db.correlation_scores.items():
                from_user_id, to_user_id = user_ids
                if user.identifier != from_user_id:
                    continue
                if to_user_id == user.identifier:
                    continue
                if not G.has_node(to_user_id):
                    other_user = self.get_user_by_id(to_user_id)
                    G.add_node(to_user_id, type=user.type,
                               color="red" if other_user.type != UserType.HONEST else "black")
                edge_color = "black"
                if correlation < -0.5:
                    edge_color = "red"
                elif correlation > 0.5:
                    edge_color = "darkgreen"

                line_thick = max(0.2, abs(correlation) * 1.5)

                G.add_edge(from_user_id, to_user_id, weight=correlation, color=edge_color, penwidth=line_thick)

        nx.nx_pydot.write_dot(G, "data/correlations.dot")

    def write_correlations(self):
        with open("data/correlations.csv", "w") as correlations_file:
            correlations_file.write("user_id,user_type,other_user_id,correlation\n")
            for user in self.users:
                for other_user_id, correlation in user.trust_db.correlation_scores.items():
                    correlations_file.write(
                        "%s,%d,%s,%.3f\n" % (user.identifier, user.type.value, other_user_id, correlation))

    def write_reputations(self):
        with open("data/reputations.csv", "w") as reputations_file:
            reputations_file.write("user_id,user_type,rule_id,reputation\n")
            for user in self.users:
                print("%s:" % user)
                for rule in user.rules_db.get_all_rules():
                    print("Reputation rule %s: %f" % (hash(rule), rule.reputation_score))
                    reputations_file.write(
                        "%s,%d,%s,%.3f\n" % (user.identifier, user.type.value, rule.rule_id, rule.reputation_score))

    def write_tags(self):
        pass

    def run(self):
        self.create_rules()
        self.create_content()
        self.create_users()
        self.create_votes()
        self.connect_users()

        for round in range(1, self.settings.rounds + 1):
            print("Evaluating round %d" % round)
            # For each user, get the voting history of other users and compute the correlation between voting histories
            for user in self.users:
                for neighbour in user.neighbours:
                    # User queries neighbours
                    neighbour_votes = neighbour.votes_db.get_random_votes(neighbour.identifier)
                    user.votes_db.add_votes(neighbour_votes)

                # TODO only update the affected items and not the entire database
                user.recompute_reputations()

        self.write_data()

    def write_data(self):
        self.write_correlation_graph()
        self.write_correlations()
        self.write_reputations()
        self.write_tags()
