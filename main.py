"""
Testing out a bare-bones scoring mechanism around voting and decentralized content rules.
"""
from asyncio import set_event_loop, ensure_future

from simulation.experiment import Experiment
from simulation.settings import ExperimentSettings
from simulation.discrete_loop import DiscreteLoop

if __name__ == "__main__":
    loop = DiscreteLoop()
    set_event_loop(loop)

    experiment_settings = ExperimentSettings(torrent_names_file_path="scripts/create_tribler_experiment/data/torrents_1000.txt")
    exp = Experiment(experiment_settings)
    ensure_future(exp.run())
    loop.run_forever()
