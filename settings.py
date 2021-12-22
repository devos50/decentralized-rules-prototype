from dataclasses import dataclass


@dataclass
class ExperimentSettings:
    num_content_items = 5
    num_rules = 3
    num_honest_users = 20
    num_adversarial_users = 1
