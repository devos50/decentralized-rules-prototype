"""
Create a scenario for the evaluation of the tagging mechanism.
"""
import random

import numpy as np

from scripts.create_movielens_experiment.generate_scenario.attack_profiles import LowerReputationAttackProfile, \
    NaiveVoteAttackProfile
from scripts.create_movielens_experiment.generate_scenario.scenario import Scenario
from scripts.create_movielens_experiment.generate_scenario.scenario_settings import ScenarioSettings

random.seed(42)
np.random.seed(42)

if __name__ == "__main__":
    settings = ScenarioSettings()
    settings.num_movies = 20
    settings.num_honest_users = 19
    settings.duration = 900

    scenario = Scenario(settings)
    scenario.generate()
    # for ind in range(5):
    #     scenario.add_attack(LowerReputationAttackProfile(target_user=0))
    for _ in range(1):
        scenario.add_attack(NaiveVoteAttackProfile(scope=0.1))
    scenario.write()

    print("Scenario generated!")
