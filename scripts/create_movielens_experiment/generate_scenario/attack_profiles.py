import random

from scripts.create_movielens_experiment.generate_scenario.action import ScenarioAction
from scripts.create_movielens_experiment.generate_scenario.scenario import Scenario


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


class NaiveDownvoteAttackProfile(AttackProfile):
    identifier = "naive_downvote"

    def __init__(self, scope: float = 1):
        super().__init__()
        self.scope = scope

    def apply(self, scenario: Scenario) -> None:
        included_tags = scenario.get_included_tags()
        user_id = self.create_new_user_in_scenario(scenario)
        tags_to_spam = random.sample(included_tags, int(len(included_tags) * self.scope))
        for movie_id, tag in tags_to_spam:
            tag_timestamp = scenario.experiment_end_time
            scenario.actions.append(ScenarioAction("vote", tag_timestamp, user_id, movie_id, tag, False))


class NaiveRandomVoteAttackProfile(AttackProfile):
    identifier = "naive_randvote"

    def __init__(self, scope: float = 1):
        super().__init__()
        self.scope = scope

    def apply(self, scenario: Scenario) -> None:
        included_tags = scenario.get_included_tags()
        user_id = self.create_new_user_in_scenario(scenario)
        tags_to_spam = random.sample(included_tags, int(len(included_tags) * self.scope))
        for movie_id, tag in tags_to_spam:
            tag_timestamp = scenario.experiment_end_time
            is_upvote = random.random() < 0.5
            scenario.actions.append(ScenarioAction("vote", tag_timestamp, user_id, movie_id, tag, is_upvote))
