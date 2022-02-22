import os
import random
from typing import Dict, Set

import networkx as nx

from core.vote import Vote
from simulation.scenario import Scenario

GENESIS_HASH = hash((0, 0, 0))

votes: Dict[int, Vote] = {}  # Keep track of the cast votes
vote_dag = nx.DiGraph()
vote_dag.add_node(GENESIS_HASH)

scenario = Scenario("create_movielens_experiment/data/scenarios/scenario_19_1")
scenario.parse()


def select_tips(action) -> Set[int]:
    tips = [node for node, in_degree in vote_dag.in_degree if in_degree == 0]
    return set(random.sample(tips, min(len(tips), 2)))


for action in scenario.actions:
    # Create a vote
    linked = select_tips(action)
    vote = Vote(action.user_id, action.movie_id, action.tag, action.is_upvote, None, None, linked)
    votes[hash(vote)] = vote

    # Extend the vote graph
    vote_dag.add_node(hash(vote))
    for linked_vote_id in vote.linked_votes:
        vote_dag.add_edge(hash(vote), linked_vote_id)


nx.nx_pydot.write_dot(vote_dag, os.path.join("..", "data", "vote_dag.dot"))
