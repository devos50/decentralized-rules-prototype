from dataclasses import dataclass


@dataclass
class ExperimentSettings:
    rounds = 100
    num_content_items = 200
    num_honest_rules = 10
    num_spam_rules = 1
    num_users = (20, 0, 0)  # Honest users, random voters, spam promotors
    content_availability = 0.3  # The percentage of all content users have

    rule_coverage = 0.1
    rule_error_rate = 0.1
    user_engagement = 0.05
    user_vote_error_rate = 0.05

    # Whether honest users upvote a few accurate rules that they classified as bad at the end of the experiment.
    do_correction_afterwards = False
