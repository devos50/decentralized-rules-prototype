import random
from typing import List, Dict, Set

from core.vote import Vote


class VotesDatabase:

    def __init__(self, my_id):
        self.my_id = my_id
        self.votes: Set[Vote] = set()
        self.votes_per_user: Dict[int, Set[Vote]] = {}
        self.votes_for_content = {}
        self.votes_for_tag: Dict[int, Dict[int, Vote]] = {}

    def add_vote(self, vote):
        self.votes.add(vote)

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
        return vote in self.votes

    def add_votes(self, votes):
        for vote in votes:
            if self.has_vote(vote):
                return

            self.add_vote(vote)

    def get_random_votes(self, limit: int = 10) -> List[Vote]:
        return random.sample(self.votes, min(len(self.votes), limit))

    def get_votes_for_user(self, user_id):
        if user_id in self.votes_per_user:
            return self.votes_per_user[user_id]
        return []

    def get_votes_for_tag(self, tag_id) -> List[Vote]:
        if tag_id in self.votes_for_tag:
            return list(self.votes_for_tag[tag_id].values())
        return []
