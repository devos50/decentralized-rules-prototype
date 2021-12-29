from dataclasses import dataclass


@dataclass
class ExperimentSettings:
    rounds = 5
    num_content_items = 8
    num_rules = 4
    num_honest_users = 5
    num_adversarial_users = 0

    rule_coverage = 0.5
    rule_error_rate = 0
    user_engagement = 1
    user_vote_error_rate = 0.25
