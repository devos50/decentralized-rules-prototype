from dataclasses import dataclass
from enum import Enum


class RuleCoverageDistribution(Enum):
    FIXED = 0
    RANDOM_UNIFORM = 1


@dataclass
class ExperimentSettings:
    rounds = 100
    num_content_items = 2000
    num_honest_rules = 10
    num_spam_rules = 1
    num_users = (20, 10, 10)  # Honest users, random voters, spam promotors
    content_availability = 0.5  # The percentage of all content users have

    rule_coverage_distribution = RuleCoverageDistribution.RANDOM_UNIFORM
    rule_coverage = 0.1
    rule_error_rate = 0.1
    initial_user_engagement = 0.05
    user_vote_error_rate = 0.05

    # Whether honest users upvote a few accurate rules that they classified as bad at the end of the experiment.
    do_correction_afterwards = False
