from dataclasses import dataclass


@dataclass
class ScenarioAction:
    command: str
    timestamp: float
    user_id: int
    movie_id: int
    tag: str
    is_upvote: bool


class Scenario:

    def __init__(self, scenario_file_path):
        self.scenario_file_path = scenario_file_path
        self.actions = []
        self.unique_users = set()

    def parse(self):
        """
        Read the scenario file and schedule the events.
        """
        print("Parsing scenario %s!" % self.scenario_file_path)
        with open(self.scenario_file_path) as scenario_file:
            for scenario_line in scenario_file:
                parts = scenario_line.strip().split(",")
                timestamp = float(parts[0])
                user_id = int(parts[1])
                movie_id = int(parts[2])
                tag = parts[3]
                is_upvote = bool(int(parts[4]))

                self.actions.append(ScenarioAction("vote", timestamp, user_id, movie_id, tag, is_upvote))
                self.unique_users.add(user_id)
        print("Parsing scenario done! Users: %d" % len(self.unique_users))
