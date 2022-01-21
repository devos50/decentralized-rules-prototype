import random
from typing import Dict, List, Set

import networkx as nx

from core.content import Content
from core.rule import Rule, RuleType
from core.tag import Tag
from core.user import User, UserType
from settings import RuleCoverageDistribution, ContentPopularityDistribution

random.seed(42)


class Experiment:

    def __init__(self, settings):
        self.settings = settings
        self.rules = []
        self.content = []
        self.content_popularity = {}
        self.users: List[User] = []
        self.round = 0

        # We keep track of the tags that are inaccurate and should be classified as such by end users.
        # Only used for experimental evaluation. In a deployed system, this information is not available.
        self.inaccurate_tags: Set[int] = set()

        # For post-experiment processing
        self.rules_reputation_per_round = {}
        self.tags_reputation_per_round = {}
        self.user_reputation_per_round = {}

    def get_user_by_id(self, user_id):
        for user in self.users:
            if user.identifier == user_id:
                return user
        return None

    def get_rule_by_id(self, rule_id):
        for rule in self.rules:
            if rule.rule_id == rule_id:
                return rule
        return None

    def create_rules(self):
        for rule_ind in range(1, self.settings.num_honest_rules + 1):
            coverage = self.settings.rule_coverage
            if self.settings.rule_coverage_distribution == RuleCoverageDistribution.RANDOM_UNIFORM:
                coverage = random.random()

            rule = Rule(rule_ind, "Tag %d" % rule_ind, coverage=coverage, error_rate=self.settings.rule_error_rate)
            rule.determine_applicable_content(self.settings.num_content_items)
            self.rules.append(rule)

        for rule_ind in range(1, self.settings.num_spam_rules + 1):
            rule = Rule(len(self.rules) + 1, "Spam %d" % rule_ind, coverage=1, error_rate=1, rule_type=RuleType.SPAM)
            rule.determine_applicable_content(self.settings.num_content_items)
            self.rules.append(rule)

    def create_content(self):
        """
        Prepare content and determine the popularity of content, according to some distribution.
        """
        self.content = [ind for ind in range(self.settings.num_content_items)]

        zipf_denom = 0
        if self.settings.content_popularity_distribution == ContentPopularityDistribution.ZIPF:
            for content_ind in range(self.settings.num_content_items):
                zipf_denom += 1 / ((content_ind + 1) ** self.settings.zipf_exponent)

        for content_ind in range(self.settings.num_content_items):
            if self.settings.content_popularity_distribution == ContentPopularityDistribution.FIXED:
                self.content_popularity[content_ind] = 1 / self.settings.num_content_items
            elif self.settings.content_popularity_distribution == ContentPopularityDistribution.ZIPF:
                self.content_popularity[content_ind] = (1 / ((content_ind + 1) ** self.settings.zipf_exponent)) / zipf_denom

    def create_users(self):
        # Create users with different profiles
        for user_type, user_num in self.settings.num_users.items():
            for user_ind in range(len(self.users) + 1, len(self.users) + user_num + 1):
                user = User("%d" % user_ind, user_type=user_type)

                if user_type == UserType.HONEST:
                    content_of_user = random.sample(self.content, int(len(self.content) * self.settings.content_availability))
                    for content_item in content_of_user:
                        user.content_db.add_content(Content("%d" % content_item, self.content_popularity[content_item]))
                else:
                    # Adversarial users have all content.
                    for content_item in self.content:
                        user.content_db.add_content(Content("%d" % content_item, self.content_popularity[content_item]))
                self.users.append(user)

        # Share and apply rules
        for user in self.users:
            user_rules = [rule.get_copy() for rule in self.rules]
            user.rules_db.add_rules(user_rules)
            user.apply_rules_to_content()

        # Create tags and share them with other users (to bootstrap the network)
        for user in self.users:
            created_tags = self.create_tags(user)
            for other_user in self.users:
                if user == other_user:
                    continue

                for tag in created_tags:
                    content = other_user.content_db.get_content(tag.cid)
                    if content:
                        added_tag = content.add_tag(tag.name, author_id=hash(user))
                        other_user.tags_db.add_tag(added_tag)

        # Create votes
        for user in self.users:
            self.create_votes(user)

    def cast_honest_user_vote(self, user, tag_to_vote_on: Tag):
        # Check if we already voted on this tag
        already_cast = False
        if tag_to_vote_on.cid in user.votes_db.votes_for_content:
            for vote in user.votes_db.votes_for_content[tag_to_vote_on.cid]:
                if tag_to_vote_on.name == vote.tag:
                    already_cast = True
                    break

        if already_cast:
            return

        # Downvote if the tag is inaccurate
        vote = True
        if hash(tag_to_vote_on) in self.inaccurate_tags:
            vote = False

        # Users sometimes vote wrong - if so, we invert the vote
        if random.random() < self.settings.user_vote_error_rate:
            print("User %s misvotes on rules %s!" % (user, tag_to_vote_on.rules))
            vote = not vote

        vote_num = 1 if vote else -1
        print("%s votes %s%d on %s (cid: %s, rules: %s, authors: %s)" % (user, "+" if vote else "", vote_num,
                                                                         tag_to_vote_on.name, tag_to_vote_on.cid,
                                                                         tag_to_vote_on.rules, tag_to_vote_on.authors))
        user.vote(tag_to_vote_on, vote)

    def create_tags(self, user: User) -> List[Tag]:
        """
        Have the specified user create some initial tags.
        """
        created_tags: List[Tag] = []
        if user.type == UserType.HONEST:
            # TODO with a uniform distribution of content
            all_content = list(user.content_db.get_all_content())
            # TODO assume that each content item receives one tag
            num_items_to_tag = min(len(all_content), int(len(all_content) * self.settings.initial_tags_created_per_user))
            content_to_tag = random.sample(all_content, num_items_to_tag)
            for content in content_to_tag:
                tag_id = hash(user) + hash(content)
                tag = user.tag(hash(content), "Tag %d" % tag_id)
                created_tags.append(tag)
        elif user.type == UserType.TAG_SPAMMER:
            # Spammers create inaccurate tags on all content they find
            for content in user.content_db.get_all_content():
                tag_id = hash(user) * 10000 + hash(content)
                tag = user.tag(hash(content), "Tag %d" % tag_id)
                created_tags.append(tag)

                self.inaccurate_tags.add(hash(tag))

        return created_tags

    def create_votes(self, user):
        """
        Create votes for the specified user
        """
        print("Creating votes for %s" % user)
        num_votes = 0

        if user.type == UserType.HONEST:
            # We will take a subset of the content and cast votes
            all_content = list(user.content_db.get_all_content())
            content_to_vote_on = random.sample(all_content, int(len(all_content) * self.settings.initial_user_engagement))
            for content in content_to_vote_on:
                for tag in content.tags:
                    if hash(user) not in tag.authors:
                        self.cast_honest_user_vote(user, tag)
                        num_votes += 1
        elif user.type == UserType.RANDOM_VOTES:
            # We simply vote randomly
            for content_item in user.content_db.get_all_content():
                for tag in content_item.tags:
                    user.vote(tag, bool(random.randint(0, 1)))
                    num_votes += 1
        elif user.type == UserType.PROMOTE_SPAM_RULES:
            # Vote honestly for accurate rules to gain goodwill with others, but promote bad rules
            for content_item in user.content_db.get_all_content():
                for tag in content_item.tags:
                    # Is this tag generated by a rule that is bad? If so, promote it. Otherwise, vote honestly.
                    generated_by_spam_rule = False
                    honest_vote = False
                    for rule_id in tag.rules:
                        rule = user.rules_db.get_rule(rule_id)
                        if rule.type == RuleType.SPAM:
                            generated_by_spam_rule = True

                        if hash(tag.cid) in rule.applicable_content_ids_correct:
                            honest_vote = True
                            break

                    if generated_by_spam_rule:
                        user.vote(tag, True)
                    else:
                        # Vote honestly
                        user.vote(tag, honest_vote)
                    num_votes += 1

        print("Created %d votes for user %s" % (num_votes, user))

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

            if user.identifier not in user.trust_db.correlation_scores:
                print("No information on %s to write correlation graph" % user)
                continue

            for to_user_id, correlation in user.trust_db.correlation_scores[user.identifier].items():
                if to_user_id == user.identifier:
                    continue  # Do not add edges to yourself
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

                G.add_edge(user.identifier, to_user_id, weight=correlation, color=edge_color, penwidth=line_thick)

        nx.nx_pydot.write_dot(G, "data/correlations.dot")

    def write_correlations(self):
        with open("data/correlations.csv", "w") as correlations_file:
            correlations_file.write("user_id,user_type,other_user_id,correlation\n")
            for user in self.users:
                if user.identifier not in user.trust_db.correlation_scores:
                    print("No information on %s to write correlation scores" % user)
                    continue

                for to_user_id, correlation in user.trust_db.correlation_scores[user.identifier].items():
                    correlations_file.write(
                        "%s,%d,%s,%.3f\n" % (user.identifier, user.type.value, to_user_id, correlation))

    def write_reputations(self):
        # Write the reputation of tags
        with open("data/tag_reputations.csv", "w") as reputations_file:
            reputations_file.write("round,user_id,tag_id,is_accurate,reputation\n")
            for round in self.tags_reputation_per_round:
                for user_id in self.tags_reputation_per_round[round]:
                    user = self.get_user_by_id(user_id)
                    if user.type != UserType.HONEST:
                        continue
                    for tag_id in self.tags_reputation_per_round[round][user_id]:
                        is_inaccurate = tag_id in self.inaccurate_tags
                        reputations_file.write(
                            "%d,%s,%d,%d,%.3f\n" % (round, user_id, tag_id, 0 if is_inaccurate else 1, self.tags_reputation_per_round[round][user_id][tag_id]))

        # Write the reputation of users
        with open("data/user_reputations.csv", "w") as reputations_file:
            reputations_file.write("round,user_id,other_user_id,reputation\n")
            for round in self.user_reputation_per_round:
                for user_id in self.user_reputation_per_round[round]:
                    user = self.get_user_by_id(user_id)
                    if user.type != UserType.HONEST:
                        continue
                    for other_user_id in self.user_reputation_per_round[round][user_id]:
                        reputations_file.write(
                            "%d,%s,%s,%.3f\n" % (round, user_id, other_user_id, self.user_reputation_per_round[round][user_id][other_user_id]))

        # Write the reputation of rules
        with open("data/rules_reputations.csv", "w") as reputations_file:
            reputations_file.write("round,user_id,rule_id,rule_type,reputation\n")
            for round in self.rules_reputation_per_round:
                for user_id in self.rules_reputation_per_round[round]:
                    user = self.get_user_by_id(user_id)
                    if user.type != UserType.HONEST:
                        continue
                    for rule_id in self.rules_reputation_per_round[round][user_id]:
                        rule = self.get_rule_by_id(rule_id)
                        reputations_file.write(
                            "%d,%s,%s,%d,%.3f\n" % (round, user_id, rule.rule_id, rule.type.value,
                                                    self.rules_reputation_per_round[round][user_id][rule_id]))

    def write_tags(self):
        """
        For each user, write all the tags in the database with the appropriate scores.
        """
        with open("data/tags.csv", "w") as tags_file:
            tags_file.write("user_id,user_type,content_id,tag,is_accurate,weight\n")
            for user in self.users:
                for content in user.content_db.get_all_content():
                    for tag in content.tags:
                        is_inaccurate = hash(tag) in self.inaccurate_tags
                        tags_file.write("%s,%s,%s,%s,%d,%f\n" % (user.identifier, user.type.value, hash(content), tag.name, 0 if is_inaccurate else 1, tag.weight))

    def run(self):
        self.create_rules()
        self.create_content()
        self.create_users()

        self.connect_users()
        self.evaluate_rounds()

    def evaluate_rounds(self):
        if self.settings.compute_reputations_per_round:
            self.recompute_all_reputations()

        for round in range(1, self.settings.rounds + 1):
            print("Evaluating round %d" % round)
            # For each user, get the voting history of other users and compute the correlation between voting histories
            for user in self.users:
                # Adversarial nodes do nothing for now
                if user.type != UserType.HONEST:
                    continue

                # Take a random content item and cast votes on the tags
                content_item = user.content_db.get_random_content_item_by_popularity()
                print("%s interacts with content %s" % (user, content_item.name))
                for tag in content_item.tags:
                    if hash(user) not in tag.authors:
                        self.cast_honest_user_vote(user, tag)

                # Exchange votes with one neighbour
                neighbour = random.choice(user.neighbours)
                neighbour_votes = neighbour.votes_db.get_random_votes(neighbour.identifier)
                user.votes_db.add_votes(neighbour_votes)
            self.round = round

            if self.settings.compute_reputations_per_round:
                self.recompute_all_reputations()

        if not self.settings.compute_reputations_per_round:
            self.recompute_all_reputations()

        if self.settings.do_correction_afterwards:
            print("Doing corrections...")
            for user in self.users:
                if user.type != UserType.HONEST:
                    continue

                did_vote = False
                for rule in user.rules_db.get_all_rules():
                    if rule.reputation_score < 0 and rule.type == RuleType.ACCURATE:
                        # Find a tag to vote for
                        for content in user.content_db.get_all_content():
                            for tag in content.tags:
                                if rule.rule_id in tag.rules:
                                    print("%s votes on rule %s (cid: %s)" % (user, rule.rule_id, tag.cid))
                                    user.vote(tag, True)
                                    did_vote = True
                                    break

                            if did_vote:
                                break

            self.recompute_all_reputations()
        self.write_data()

    def recompute_all_reputations(self):
        self.rules_reputation_per_round[self.round] = {}
        self.user_reputation_per_round[self.round] = {}
        self.tags_reputation_per_round[self.round] = {}
        for user in self.users:
            user.recompute_reputations()
            self.rules_reputation_per_round[self.round][user.identifier] = {}
            self.user_reputation_per_round[self.round][user.identifier] = {}
            self.tags_reputation_per_round[self.round][user.identifier] = {}
            for rule in user.rules_db.get_all_rules():
                print("Reputation rule %s: %f" % (hash(rule), rule.reputation_score))
                self.rules_reputation_per_round[self.round][user.identifier][rule.rule_id] = rule.reputation_score
            for other_user_id, user_rep in user.trust_db.user_reputations.items():
                print("Reputation of user %s: %f" % (other_user_id, user_rep))
                self.user_reputation_per_round[self.round][user.identifier][other_user_id] = user_rep
            for tag in user.tags_db.get_all_tags():
                print("Reputation tag %s: %f" % (hash(tag), tag.reputation_score))
                self.tags_reputation_per_round[self.round][user.identifier][hash(tag)] = tag.reputation_score

    def write_data(self):
        self.write_correlation_graph()
        self.write_correlations()
        self.write_reputations()
        self.write_tags()
