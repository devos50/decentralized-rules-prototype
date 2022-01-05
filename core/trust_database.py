import math
from enum import Enum

import networkx as nx
from numpy import average

from core.vote import Vote


class SimilarityMetric(Enum):
    PHI_CORRELATION = 0
    JACCARD = 1


class TrustDatabase:

    def __init__(self, my_id, votes_db):
        self.my_id = my_id
        self.correlation_scores = {}
        self.max_flows = {}
        self.votes_db = votes_db

    def compute_correlations(self, similarity_metric):
        """
        Compute the correlation scores to all neighbours, based on the acquired local knowledge.
        """
        self.correlation_scores = {}
        for uid1 in self.votes_db.votes.keys():
            for uid2 in self.votes_db.votes.keys():
                if uid1 == uid2 and uid1 != self.my_id:
                    continue
                correlation = self.compute_correlation_coefficient(uid1, uid2, similarity_metric)

                if uid1 not in self.correlation_scores:
                    self.correlation_scores[uid1] = {}
                if uid2 not in self.correlation_scores:
                    self.correlation_scores[uid1][uid2] = []

                self.correlation_scores[uid1][uid2] = correlation

    def get_correlation_coefficient(self, uid1, uid2):
        return self.correlation_scores[uid1][uid2] if uid1 in self.correlation_scores and uid2 in self.correlation_scores[uid1] else 0

    def compute_correlation_coefficient(self, user_a, user_b, similarity_metric):
        """
        Compute the correlation coefficient from the perspective of this user.
        """
        votes = {}  # Rule => ([...], [...])

        for vote in self.votes_db.get_votes_for_user(user_a):
            for rule_id in vote.rules_ids:
                if rule_id not in votes:
                    votes[rule_id] = ([], [])
                votes[rule_id][0].append(1 if vote.is_accurate else -1)

        for vote in self.votes_db.get_votes_for_user(user_b):
            for rule_id in vote.rules_ids:
                if rule_id not in votes:
                    votes[rule_id] = ([], [])
                votes[rule_id][1].append(1 if vote.is_accurate else -1)

        # print("Votes between %s and %s: %s" % (user_a, user_b, votes))

        # For each rule, we compute the average rating by each user and compute the absolute difference.
        # weights = []
        diffs = []
        for rule_id, votes in votes.items():
            votes_a, votes_b = votes
            if not votes_a or not votes_b:
                continue  # No overlap to work with

            diffs.append(abs(average(votes_a) - average(votes_b)))
            # weights.append(min(len(votes_a), len(votes_b)))

        # # Normalize weights
        # weights_sum = sum(weights)
        # for ind in range(len(weights)):
        #     weights[ind] /= weights_sum
        #
        # # Compute the weighted average
        # diffs_avg = 0
        # for ind in range(len(diffs)):
        #     diffs_avg += weights[ind] * diffs[ind]


        #print("Computing correlation between user %s and %s" % (user_a, user_b))

        # votes_agree, votes_conflict = Vote.get_overlap(self.votes_db.get_votes_for_user(user_a),
        #                                                self.votes_db.get_votes_for_user(user_b))
        # print("Votes agree: %d, votes conflict: %d" % (len(votes_agree), len(votes_conflict)))

        if not diffs:
            return 0

        return 1 - average(diffs)

        # total_vote_pairs = len(votes_agree) + len(votes_conflict)
        # if similarity_metric == SimilarityMetric.PHI_CORRELATION:
        #     if total_vote_pairs == 0:
        #         return 0  # No overlap at all
        #     a_abs, b_abs, p_abs = 0, 0, 0
        #     for vote_a, vote_b in votes_agree:
        #         if vote_a.is_accurate:
        #             p_abs += 1
        #     p = p_abs / total_vote_pairs
        #
        #     # Find number of positive votes from a and b respectively
        #     for vote_a, vote_b in votes_agree.union(votes_conflict):
        #         if vote_a.is_accurate:
        #             a_abs += 1
        #         if vote_b.is_accurate:
        #             b_abs += 1
        #
        #     a = a_abs / total_vote_pairs
        #     b = b_abs / total_vote_pairs
        #     #print("Vote pairs: %d, p: %d, a: %d, b: %d" % (total_vote_pairs, p_abs, a_abs, b_abs))
        #
        #     # If a or b is 0 or 1, a user voted positively or negatively on all objects. In this case, rho is undefined.
        #     # In this case, we simply compute the fraction of votes that agree and project this fraction to the interval
        #     # [-1, 1].
        #     if a == 0 or b == 0 or a == 1 or b == 1:
        #         return (len(votes_agree) / total_vote_pairs) * 2 - 1
        #
        #     correlation = (p - a * b) / math.sqrt(a * (1 - a) * b * (1 - b))
        #     return correlation
        # elif similarity_metric == SimilarityMetric.JACCARD:
        #     if total_vote_pairs == 0:
        #         return 0
        #     correlation = (len(votes_agree) / total_vote_pairs) * 2 - 1
        #     print("Votes agree: %d, total pairs: %d, correlation: %f" % (len(votes_agree), total_vote_pairs, correlation))
        #     return correlation

    def compute_flows(self):
        self.max_flows = {}

        # Construct the flow graph
        other_user_ids = set()
        flow_graph = nx.Graph()
        for from_user_id in self.correlation_scores.keys():
            for to_user_id, score in self.correlation_scores[from_user_id].items():
                if from_user_id == self.my_id and to_user_id == self.my_id:
                    continue

                if from_user_id == self.my_id and to_user_id != self.my_id:
                    other_user_ids.add(to_user_id)
                flow_graph.add_edge(from_user_id, to_user_id, capacity=score)

        for other_user_id in other_user_ids:
            flow_value, _ = nx.maximum_flow(flow_graph, self.my_id, other_user_id)
            self.max_flows[other_user_id] = flow_value

        # Your own flow is the sum of flows to the other nodes.
        # This ensures that your opinion is weighted in with 50%.
        self.max_flows[self.my_id] = sum(self.max_flows.values())
