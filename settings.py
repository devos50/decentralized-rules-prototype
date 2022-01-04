from dataclasses import dataclass


@dataclass
class ExperimentSettings:
    rounds = 100
    num_content_items = 200
    num_honest_rules = 10
    num_spam_rules = 2
    num_users = (10, 10, 10)  # Honest users, random voters, spam promotors

    rule_coverage = 0.25
    rule_error_rate = 0.1
    user_engagement = 0.05
    user_vote_error_rate = 0.05
    # TODO not all users have all content - model this
