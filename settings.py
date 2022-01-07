from dataclasses import dataclass
from enum import Enum


class RuleCoverageDistribution(Enum):
    FIXED = 0
    RANDOM_UNIFORM = 1


class ContentPopularityDistribution(Enum):
    FIXED = 0
    ZIPF = 1


@dataclass
class ExperimentSettings:
    rounds = 100

    # Content parameters
    num_content_items = 200
    content_availability = 1  # The percentage of all content users have
    zipf_exponent = 1
    content_popularity_distribution = ContentPopularityDistribution.ZIPF

    # Rule parameters
    num_honest_rules = 10
    num_spam_rules = 1
    rule_coverage_distribution = RuleCoverageDistribution.RANDOM_UNIFORM
    rule_coverage = 0.1
    rule_error_rate = 0.1

    # User parameters
    num_users = (20, 0, 0)  # Honest users, random voters, spam promotors
    initial_user_engagement = 0.05
    user_vote_error_rate = 0.05

    # Whether honest users upvote a few accurate rules that they classified as bad at the end of the experiment.
    do_correction_afterwards = False
