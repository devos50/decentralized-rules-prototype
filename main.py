"""
Testing out a bare-bones scoring mechanism around voting and decentralized content rules.
"""
from experiment import Experiment
from settings import ExperimentSettings

experiment_settings = ExperimentSettings()
exp = Experiment(experiment_settings)
exp.run()
