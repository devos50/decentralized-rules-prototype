import csv
import os
from dataclasses import dataclass
from typing import List


@dataclass
class ScenarioAction:
    command: str
    timestamp: float
    user_id: int
    movie_id: int
    tag: str
    is_upvote: bool


class Scenario:

    def __init__(self, scenario_dir):
        self.scenario_dir = scenario_dir
        self.actions: List[ScenarioAction] = []
        self.unique_users = set()
        self.users_by_type = {}

    def parse(self):
        """
        Read the scenario file and schedule the events.
        """
        scenario_file_path = os.path.join(self.scenario_dir, "experiment.scenario")
        print("Parsing scenario %s!" % scenario_file_path)
        with open(scenario_file_path) as scenario_file:
            for scenario_line in scenario_file:
                parts = scenario_line.strip().split(",")
                timestamp = float(parts[0])
                command = parts[1]
                user_id = int(parts[2])
                movie_id = int(parts[3])
                tag = parts[4]
                is_upvote = bool(int(parts[5]))

                self.actions.append(ScenarioAction(command, timestamp, user_id, movie_id, tag, is_upvote))
                self.unique_users.add(user_id)

        users_file_path = os.path.join(self.scenario_dir, "users.csv")
        with open(users_file_path) as user_file:
            csv_reader = csv.reader(user_file)
            next(csv_reader)  # Skip header
            for row in csv_reader:
                user_id = int(row[0])
                user_type = int(row[1])
                if user_type not in self.users_by_type:
                    self.users_by_type[user_type] = []
                self.users_by_type[user_type].append(user_id)

        print("Parsing scenario done! Users: %d" % len(self.unique_users))
