from dataclasses import dataclass
from enum import Enum

from core.user import UserType


class RuleCoverageDistribution(Enum):
    FIXED = 0
    RANDOM_UNIFORM = 1


class ContentPopularityDistribution(Enum):
    FIXED = 0
    ZIPF = 1


@dataclass
class ExperimentSettings:
    duration = 3600  # Experiment duration in seconds
    scenario_dir = None

    # Gossip parameters
    exchange_interval = 5
    gossip_batch_size = 20

    # Content parameters
    num_content_items = 1
    content_availability = 1  # The percentage of all content users have
    zipf_exponent = 1
    content_popularity_distribution = ContentPopularityDistribution.FIXED

    # Rule parameters
    num_honest_rules = 1
    rule_coverage_distribution = RuleCoverageDistribution.FIXED
    rule_coverage = 1
    rule_error_rate = 0

    # User parameters
    num_users = {
        # Honest user - attempts to vote faithfully.
        UserType.HONEST: 0
    }
    initial_user_engagement = 1
    initial_tags_created_per_user = 0  # TODO should follow a power-law
    user_vote_error_rate = 0

    # Whether honest users upvote a few accurate rules that they classified as bad at the end of the experiment.
    do_correction_afterwards = False

    # Whether we (re)compute all reputation scores every round.
    compute_reputations_per_round = False
