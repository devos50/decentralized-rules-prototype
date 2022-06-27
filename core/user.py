import random
from asyncio import sleep
from enum import Enum
from typing import List

from core.db.content_database import ContentDatabase
from core.db.peers_database import PeersDatabase
from core.db.rules_database import RulesDatabase
from core.knowledge_graph import KnowledgeGraph


class UserType(Enum):
    HONEST = "honest"
    CREATE_INACCURATE_TAGS = "bad_tagger"
    NAIVE_NEGATIVE_VOTER = "naive_downvote"
    NAIVE_POSITIVE_VOTER = "naive_upvote"
    NAIVE_RANDOM_VOTER = "naive_randvote"
    FIXED_NAIVE_NEGATIVE_VOTER = "fixed_naive_downvote"
    FIXED_NAIVE_POSITIVE_VOTER = "fixed_naive_upvote"
    FIXED_NAIVE_RANDOM_VOTER = "fixed_naive_randvote"
    LOWER_REPUTATION = "lower_reputation"


class User:

    def __init__(self, identifier, user_type=UserType.HONEST):
        self.identifier = identifier
        self.peers_db = PeersDatabase()
        self.rules_db = RulesDatabase()
        self.content_db = ContentDatabase()
        self.knowledge_graph = KnowledgeGraph()
        self.neighbours: List[User] = []
        self.type = user_type

    def connect(self, other_user):
        self.neighbours.append(other_user)
        self.peers_db.add_peer(hash(other_user))

    def apply_rules(self):
        # TODO rules might be applied in batches
        for rule in self.rules_db.get_all_rules():
            for content in self.content_db.get_all_content():
                triplets = rule.apply_rule(content)
                for triplet in triplets:
                    self.knowledge_graph.add_triplet(triplet)

    async def start_graph_exchange(self, graph_exchange_interval: int, edge_batch_size: int):
        while True:
            neighbour = random.choice(self.neighbours)
            triplets = self.knowledge_graph.get_random_edges(limit=edge_batch_size)
            for triplet in triplets:
                neighbour.process_incoming_triplet(triplet)
            await sleep(graph_exchange_interval)

    def process_incoming_triplet(self, triplet):
        self.knowledge_graph.add_triplet(triplet)

    def __str__(self):
        return "User %s (%s)" % (hash(self), self.type.value)

    def __hash__(self):
        return int(self.identifier)
