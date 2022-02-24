import random
from enum import Enum

from scripts.create_movielens_experiment.generate_scenario.action import ScenarioAction
from scripts.create_movielens_experiment.generate_scenario.scenario import Scenario


class VoteType(Enum):
    UPVOTE = 0
    DOWNVOTE = 1
    RANDOM = 2


class AttackProfile:
    identifier = "unknown"

    def __init__(self):
        pass

    def apply(self, scenario: Scenario) -> None:
        pass

    def create_new_user_in_scenario(self, scenario: Scenario) -> int:
        # Add the user to the scenario
        user_id = scenario.total_users
        scenario.total_users += 1
        if self.identifier not in scenario.users_by_type:
            scenario.users_by_type[self.identifier] = []
        scenario.users_by_type[self.identifier].append(user_id)
        return user_id


class NaiveVoteAttackProfile(AttackProfile):
    identifier = "naive_vote"

    def __init__(self, scope: float = 1, vote_type: VoteType = VoteType.DOWNVOTE):
        super().__init__()
        self.scope = scope
        self.vote_type = vote_type
        self.identifier = "naive_downvote" if vote_type == VoteType.DOWNVOTE else \
            "naive_upvote" if vote_type == VoteType.UPVOTE else "naive_randvote"

    def apply(self, scenario: Scenario) -> None:
        self.create_new_user_in_scenario(scenario)


class FixedNaiveVoteAttackProfile(AttackProfile):
    """
    With this attack profile, the votes cast by the adversary are embedded in the scenario file.
    """
    identifier = "fixed_naive_vote"

    def __init__(self, scope: float = 1, vote_type: VoteType = VoteType.DOWNVOTE):
        super().__init__()
        self.scope = scope
        self.vote_type = vote_type
        self.identifier = "fixed_naive_downvote" if vote_type == VoteType.DOWNVOTE else \
            "fixed_naive_upvote" if vote_type == VoteType.UPVOTE else "fixed_naive_randvote"

    def apply(self, scenario: Scenario) -> None:
        included_tags = scenario.get_included_tags()
        user_id = self.create_new_user_in_scenario(scenario)
        tags_to_spam = random.sample(included_tags, int(len(included_tags) * self.scope))
        for movie_id, tag in tags_to_spam:
            tag_timestamp = scenario.experiment_end_time

            vote = None
            if self.vote_type == VoteType.DOWNVOTE:
                vote = False
            elif self.vote_type == VoteType.UPVOTE:
                vote = True
            elif self.vote_type == VoteType.RANDOM:
                vote = random.random() < 0.5

            scenario.actions.append(ScenarioAction("vote", tag_timestamp, user_id, movie_id, tag, vote))


class LowerReputationAttackProfile(AttackProfile):
    """
    With this attack, a user attempts to lower the reputation of another peer. It does so by:
    - Downvoting tags created by the target user.
    - Vote the opposite of what the target user voted on a particular tag.
    - if the target user is unrelated to a tag, the attacker follows the majority vote on a tag.
    """
    identifier = "lower_reputation"

    def __init__(self, target_user: int = 0):
        super().__init__()
        self.target_user = target_user

    def apply(self, scenario: Scenario) -> None:
        user_id = self.create_new_user_in_scenario(scenario)
        for tag in scenario.tags_info.values():
            vote = None
            if tag.author == self.target_user:
                vote = False
            elif self.target_user in tag.upvotes:
                vote = False
            elif self.target_user in tag.downvotes:
                vote = True

            if vote is None and tag.upvotes != tag.downvotes:
                # Simply vote what the majority voted
                vote = len(tag.upvotes) > len(tag.downvotes)

            if vote is not None:
                scenario.actions.append(ScenarioAction("vote", scenario.experiment_end_time, user_id, tag.movie_id, tag.tag, vote))
