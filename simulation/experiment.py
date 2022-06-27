import json
import random
from asyncio import sleep, get_event_loop, ensure_future
from typing import List

from networkx.readwrite import json_graph

from core.content import Content
from core.rules.ptn import PTNRule
from core.user import User

from simulation.settings import ExperimentSettings

random.seed(42)


class Experiment:

    def __init__(self, settings: ExperimentSettings):
        self.settings = settings
        self.rules = []
        self.content: List[Content] = []
        self.users: List[User] = []

    def get_user_by_id(self, user_id: int):
        for user in self.users:
            if hash(user) == user_id:
                return user
        return None

    def get_rule_by_id(self, rule_id):
        for rule in self.rules:
            if rule.rule_id == rule_id:
                return rule
        return None

    def parse_content(self):
        """
        Read content from the torrent filenames database.
        """
        with open(self.settings.torrent_names_file_path, "rb") as torrent_names_file:
            for line in torrent_names_file.readlines():
                self.content.append(Content(line.strip()))

        print("Parsed %d torrent file names" % len(self.content))

    def create_users(self):
        for user_ind in range(self.settings.num_users):
            user = User("%d" % user_ind)
            self.users.append(user)

    def connect_users(self):
        # Create a strongly connected graph
        for user_a in self.users:
            for user_b in self.users:
                if user_a == user_b:
                    continue
                user_a.connect(user_b)

    def distribute_content(self):
        for ind, content in enumerate(self.content):
            self.users[ind % len(self.users)].content_db.add_content(content)

    def distribute_rules(self):
        for user in self.users:
            user.rules_db.add_rule(PTNRule())

    def apply_rules(self):
        for user in self.users:
            user.apply_rules()
        print("All user applied all rules")

    async def run(self):
        self.parse_content()
        self.create_users()
        self.distribute_content()
        self.distribute_rules()
        self.apply_rules()
        self.connect_users()

        # Start the routine for exchanging graph entries
        loop = get_event_loop()
        for user in self.users:
            loop.call_later(random.randint(0, self.settings.edge_exchange_interval),
                            lambda u=user: ensure_future(u.start_graph_exchange(self.settings.edge_exchange_interval,
                                                                                self.settings.edge_batch_size)))

        await sleep(self.settings.duration)

        loop = get_event_loop()
        loop.stop()
