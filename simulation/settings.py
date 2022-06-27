from dataclasses import dataclass


@dataclass
class ExperimentSettings:
    duration = 3600  # Experiment duration in seconds
    torrent_names_file_path: str
    num_users = 5
    edge_exchange_interval = 5
    edge_batch_size = 10
