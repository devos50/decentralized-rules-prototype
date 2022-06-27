from dataclasses import dataclass


@dataclass
class ExperimentSettings:
    duration = 7200  # Experiment duration in seconds
    num_users = 20
    edge_exchange_interval = 5
    edge_batch_size = 10
    data_dir: str = ""
