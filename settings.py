from dataclasses import dataclass


@dataclass
class ExperimentSettings:
    rounds = 10
    num_content_items = 1
    num_honest_rules = 2
    num_spam_rules = 1
    num_users = (2, 0, 1)  # Honest users, random voters, spam promotors

    rule_coverage = 1
    rule_error_rate = 0
    user_engagement = 1
    user_vote_error_rate = 0
    # TODO not all users have all content - model this
