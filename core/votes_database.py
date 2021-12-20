import math
import random

from core.vote import Vote


class VotesDatabase:

    def __init__(self, my_id):
        self.my_id = my_id
        self.votes = {}
        self.votes_for_rules = {}
        self.correlation_scores = {}

    def add_vote(self, vote):
        if vote.user_id not in self.votes:
            self.votes[vote.user_id] = set()
        self.votes[vote.user_id].add(vote)

        for rule_id in vote.rules_ids:
            if rule_id not in self.votes_for_rules:
                self.votes_for_rules[rule_id] = []
            self.votes_for_rules[rule_id].append(vote)

    def add_votes(self, votes):
        for vote in votes:
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

    def compute_correlations(self):
        """
        Compute the correlation scores to all neighbours.
        """
        self.correlation_scores = {}
        for other_peer_id in self.votes.keys():
            self.correlation_scores[other_peer_id] = self.compute_correlation_coefficient(self.my_id, other_peer_id)

    def get_correlation_coefficient(self, other_user_id):
        return self.correlation_scores[other_user_id] if other_user_id in self.correlation_scores else 0

    def compute_correlation_coefficient(self, user_a, user_b):
        """
        Compute the correlation coefficient from the perspective of this user.
        """
        votes_agree, votes_conflict = Vote.get_overlap(self.get_votes_for_user(user_a), self.get_votes_for_user(user_b))
        total_vote_pairs = len(votes_agree) + len(votes_conflict)
        if total_vote_pairs == 0:
            return 0  # No overlap at all
        a_abs, b_abs, p_abs = 0, 0, 0
        for vote_a, vote_b in votes_agree:
            if vote_a.is_accurate:
                p_abs += 1
        p = p_abs / total_vote_pairs

        # Find number of positive votes from a and b respectively
        for vote_a, vote_b in votes_agree.union(votes_conflict):
            if vote_a.is_accurate:
                a_abs += 1
            if vote_b.is_accurate:
                b_abs += 1

        a = a_abs / total_vote_pairs
        b = b_abs / total_vote_pairs

        # If a or b is 0 or 1, a user voted positively or negatively on all objects. In this case, rho is undefined.
        # In this case, we simply compute the fraction of votes that agree and project this fraction to the interval
        # [-1, 1].
        if a == 0 or b == 0 or a == 1 or b == 1:
            return (len(votes_agree) / total_vote_pairs) * 2 - 1

        return (p - a * b) / math.sqrt(a * (1 - a) * b * (1 - b))
