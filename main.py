"""
Testing out a bare-bones scoring mechanism around voting and decentralized content rules.
"""
from experiment import Experiment
from settings import ExperimentSettings

if __name__ == "__main__":
    experiment_settings = ExperimentSettings()
    exp = Experiment(experiment_settings)
    exp.run()
