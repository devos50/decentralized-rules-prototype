import random
from typing import Tuple

import networkx as nx


class KnowledgeGraph:
    """
    Represents the local knowledge graph.
    """

    def __init__(self) -> None:
        self.graph = nx.DiGraph()

    def add_triplet(self, triplet: Tuple[str, str, str]) -> None:
        self.graph.add_edge(triplet[0], triplet[2], attr={"relation": triplet[1]})

    def get_random_edges(self, limit=10):
        random_edges = random.sample(self.graph.edges, limit)
        # Get the relations
        triplets = set()
        for random_edge in random_edges:
            relation = self.graph.edges[random_edge]["attr"]["relation"]
            triplet = (random_edge[0], relation, random_edge[1])
            triplets.add(triplet)
        return triplets
