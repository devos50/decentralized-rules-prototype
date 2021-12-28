"""
Testing out a bare-bones scoring mechanism around voting and decentralized content rules.
"""
import random

import networkx as nx

from core.content import Content
from core.rule import Rule
from core.user import User, UserType
from settings import ExperimentSettings

experiment_settings = ExperimentSettings()

# Create rules
rules = []
for rule_ind in range(1, experiment_settings.num_rules + 1):
    rule = Rule(rule_ind, "Tag %d" % rule_ind)
    rule.determine_applicable_content(experiment_settings.num_content_items)
    rules.append(rule)

# Create content
content = []
for content_ind in range(experiment_settings.num_content_items):
    content.append("%d" % content_ind)

# Create users
users = []
for user_ind in range(1, experiment_settings.num_honest_users + 1):
    user = User("%d" % user_ind)
    for content_item in content:
        user.content_db.add_content(Content(content_item))
    users.append(user)

# Create adversarial users
for user_ind in range(len(users) + 1, len(users) + experiment_settings.num_adversarial_users + 1):
    user = User("%d" % user_ind, user_type=UserType.RANDOM_VOTES)
    for content_item in content:  # Adversarial users have all content.
        user.content_db.add_content(Content(content_item))
    users.append(user)

# Distribute rules over users
for user in users:
    user_rules = [rule.get_copy() for rule in rules]
    user.rules_db.add_rules(user_rules)
    user.apply_rules_to_content()

# Create some votes
for user in users:
    for content_item in user.content_db.get_all_content():
        for tag in content_item.tags:
            vote = True
            if user.type == UserType.RANDOM_VOTES:
                vote = bool(random.randint(0, 1))
            user.vote(tag, vote)


# Create a strongly connected graph
for user_a in users:
    for user_b in users:
        if user_a == user_b:
            continue
        user_a.connect(user_b)

rounds = 5
for round in range(1, rounds + 1):
    print("Evaluating round %d" % round)
    # For each user, get the voting history of other users and compute the correlation between voting histories
    for user in users:
        for neighbour in user.neighbours:
            # User queries neighbours
            neighbour_votes = neighbour.votes_db.get_random_votes(neighbour.identifier)
            user.votes_db.add_votes(neighbour_votes)

        # TODO only update the affected items and not the entire database
        user.recompute_reputations()


def get_user_by_id(user_id):
    for user in users:
        if user.identifier == user_id:
            return user
    return None


# Create correlation graph
G = nx.DiGraph()
for user in users:
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
            other_user = get_user_by_id(to_user_id)
            G.add_node(to_user_id, type=user.type, color="red" if other_user.type != UserType.HONEST else "black")
        edge_color = "black"
        if correlation < -0.5:
            edge_color = "red"
        elif correlation > 0.5:
            edge_color = "darkgreen"

        line_thick = max(0.2, abs(correlation) * 1.5)

        G.add_edge(from_user_id, to_user_id, weight=correlation, color=edge_color, penwidth=line_thick)

nx.nx_pydot.write_dot(G, "data/correlations.dot")

with open("data/correlations.csv", "w") as correlations_file:
    correlations_file.write("user_id,user_type,other_user_id,correlation\n")
    for user in users:
        for other_user_id, correlation in user.trust_db.correlation_scores.items():
            correlations_file.write("%s,%d,%s,%.3f\n" % (user.identifier, user.type.value, other_user_id, correlation))

with open("data/reputations.csv", "w") as reputations_file:
    reputations_file.write("user_id,user_type,rule_id,reputation\n")
    for user in users:
        print("%s:" % user)
        for rule in user.rules_db.get_all_rules():
            print("Reputation rule %s: %f" % (hash(rule), rule.reputation_score))
            reputations_file.write("%s,%d,%s,%.3f\n" % (user.identifier, user.type.value, rule.rule_id, rule.reputation_score))
