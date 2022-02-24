import random
from typing import List, Dict, Set, Optional

import networkx as nx

from core import GENESIS_HASH
from core.vote import Vote


class VotesDatabase:

    def __init__(self, my_id):
        self.my_id = my_id
        self.votes: Dict[int, Vote] = {}
        self.votes_per_user: Dict[int, Set[Vote]] = {}
        self.votes_for_content = {}
        self.votes_for_tag: Dict[int, Dict[int, Vote]] = {}

        self.vote_dag = nx.DiGraph()
        self.vote_dag.add_node(GENESIS_HASH)

    def add_vote(self, vote):
        self.votes[hash(vote)] = vote

        # Extend the vote DAG
        for linked_vote_id in vote.linked_votes:
            self.vote_dag.add_edge(hash(vote), linked_vote_id)

        if vote.user_id not in self.votes_per_user:
            self.votes_per_user[vote.user_id] = set()
        self.votes_per_user[vote.user_id].add(vote)

        if vote.cid not in self.votes_for_content:
            self.votes_for_content[vote.cid] = []
        self.votes_for_content[vote.cid].append(vote)

        tag_hash = hash((vote.cid, vote.tag))
        if tag_hash not in self.votes_for_tag:
            self.votes_for_tag[tag_hash] = {}
        if vote.user_id not in self.votes_for_tag[tag_hash]:
            self.votes_for_tag[tag_hash][vote.user_id] = vote

    def has_vote(self, vote):
        return hash(vote) in self.votes

    def add_votes(self, votes):
        for vote in votes:
            if self.has_vote(vote):
                return

            self.add_vote(vote)

    def get_random_votes(self, limit: int = 10, exclude: Optional[int] = None) -> List[Vote]:
        """
        Sample random votes from the database.
        :param limit: The maximum number of votes to sample.
        :param exclude: Whether to exclude the votes of a particular user.
        :return: A list of sampled votes.
        """
        if exclude:
            eligible_votes = [vote for vote in self.votes.values() if vote.user_id != exclude]
        else:
            eligible_votes = list(self.votes.values())
        return random.sample(eligible_votes, min(len(eligible_votes), limit))

    def get_votes_for_user(self, user_id):
        if user_id in self.votes_per_user:
            return self.votes_per_user[user_id]
        return []

    def get_votes_for_tag(self, tag_id) -> List[Vote]:
        if tag_id in self.votes_for_tag:
            return list(self.votes_for_tag[tag_id].values())
        return []

    def user_did_vote_for_tag(self, user_id, cid, tag) -> bool:
        if user_id not in self.votes_per_user:
            return False
        for vote in self.votes_per_user[user_id]:
            if vote.cid == cid and vote.tag == tag:
                return True
        return False
