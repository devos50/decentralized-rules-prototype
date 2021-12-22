"""
Testing out a bare-bones scoring mechanism around voting and decentralized content rules.
"""
from core.content import Content
from core.rule import Rule
from core.user import User

NUM_RULES = 2
NUM_USERS = 3
NUM_CONTENT = 10

# Create rules
rules = []
for rule_ind in range(NUM_RULES):
    rule = Rule("Tag %d" % rule_ind)
    rule.determine_applicable_content(NUM_CONTENT)
    rules.append(rule)

# Create content
content = []
for content_ind in range(NUM_CONTENT):
    content.append("%d" % content_ind)

# Create users
users = []
for user_ind in range(1, NUM_USERS + 1):
    user = User("%d" % user_ind)
    for content_item in content:
        user.content_db.add_content(Content(content_item))
    users.append(user)

# Distribute rules over users
for user in users:
    user.rules_db.add_rules(rules)
    user.apply_rules_to_content()

# Create some votes
for user in users:
    for content_item in user.content_db.get_all_content():
        for tag in content_item.tags:
            user.vote(tag, True)

# Create a strongly connected graph
for user_a in users:
    for user_b in users:
        if user_a == user_b:
            continue
        user_a.connect(user_b)

rounds = 1
for round in range(1, rounds + 1):
    print("Evaluating round %d" % round)
    # For each user, get the voting history of other users and compute the correlation between voting histories
    for user in users:
        for neighbour in user.neighbours:
            # User queries neighbour
            neighbour_votes = neighbour.votes_db.get_random_votes(neighbour.identifier)
            user.votes_db.add_votes(neighbour_votes)

            # TODO only update the affected items and not the entire database
            user.recompute_reputations()


# Print reputations
for user in users:
    print("User %s:" % user.identifier)
    for rule in user.rules_db.get_all_rules():
        print("Reputation rule %s: %f" % (hash(rule), rule.reputation_score))
