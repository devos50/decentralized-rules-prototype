import random
from typing import List

from core.vote import Vote


class VotesDatabase:

    def __init__(self, my_id):
        self.my_id = my_id
        self.votes = {}
        self.votes_for_rules = {}
        self.votes_for_content = {}
        self.votes_for_tag = {}

    def add_vote(self, vote):
        if vote.user_id not in self.votes:
            self.votes[vote.user_id] = set()
        self.votes[vote.user_id].add(vote)

        for rule_id in vote.rules_ids:
            if rule_id not in self.votes_for_rules:
                self.votes_for_rules[rule_id] = []
            self.votes_for_rules[rule_id].append(vote)

        if vote.cid not in self.votes_for_content:
            self.votes_for_content[vote.cid] = []
        self.votes_for_content[vote.cid].append(vote)

        tag_hash = hash((vote.cid, vote.tag))
        if tag_hash not in self.votes_for_tag:
            self.votes_for_tag[tag_hash] = []
        self.votes_for_tag[tag_hash].append(vote)

    def has_vote(self, vote):
        if vote.user_id not in self.votes:
            return False
        return vote in self.votes[vote.user_id]

    def add_votes(self, votes):
        for vote in votes:
            if self.has_vote(vote):
                return

            self.add_vote(vote)

    def get_random_votes(self, user_id, limit=10):
        if user_id not in self.votes:
            return []
        user_votes = list(self.get_votes_for_user(user_id))
        return random.sample(user_votes, min(len(user_votes), limit))

    def get_votes_for_user(self, user_id):
        if user_id in self.votes:
            return self.votes[user_id]
        return []

    def get_votes_for_rule(self, rule_id):
        if rule_id in self.votes_for_rules:
            return self.votes_for_rules[rule_id]
        return []

    def get_votes_for_tag(self, tag_id) -> List[Vote]:
        if tag_id in self.votes_for_tag:
            return self.votes_for_tag[tag_id]
        return []
