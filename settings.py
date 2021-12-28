from dataclasses import dataclass


@dataclass
class ExperimentSettings:
    num_content_items = 5
    num_rules = 4
    num_honest_users = 6
    num_adversarial_users = 0
