from enum import Enum

from core.content_database import ContentDatabase
from core.rules_database import RulesDatabase
from core.trust_database import TrustDatabase, SimilarityMetric
from core.vote import Vote
from core.votes_database import VotesDatabase


class UserType(Enum):
    HONEST = 0
    RANDOM_VOTES = 1


class User:

    def __init__(self, identifier, user_type=UserType.HONEST, similarity_metric=SimilarityMetric.JACCARD):
        self.identifier = identifier
        self.content_db = ContentDatabase()
        self.rules_db = RulesDatabase()
        self.votes_db = VotesDatabase(self.identifier)
        self.trust_db = TrustDatabase(self.identifier, self.votes_db)
        self.neighbours = []
        self.type = user_type
        self.similarity_metric = similarity_metric

    def connect(self, other_user):
        self.neighbours.append(other_user)

    def vote(self, tag, is_accurate):
        content_item = self.content_db.get_content(tag.cid)
        if not content_item:
            raise RuntimeError("Content item with ID %s not found in the database of user %s!" % (tag.cid, self.identifier))

        vote = Vote(self.identifier, tag.cid, tag.name, tag.rules, is_accurate)
        self.votes_db.add_vote(vote)

    def apply_rules_to_content(self):
        for rule in self.rules_db.get_all_rules():
            self.content_db.apply_rule(rule)

    def recompute_reputations(self):
        # Compute correlations
        self.trust_db.compute_correlations(self.similarity_metric)

        # Compute max flows between pairs
        self.trust_db.compute_flows()

        # Compute rule reputations
        for rule in self.rules_db.get_all_rules():
            votes_for_rule = self.votes_db.get_votes_for_rule(hash(rule))
            if not votes_for_rule:
                rule.reputation_score = 0
                continue

            rep_fractions = {}
            num_votes_per_user = {}
            for vote in votes_for_rule:
                if vote.user_id not in rep_fractions:
                    rep_fractions[vote.user_id] = 0
                    num_votes_per_user[vote.user_id] = 0

                bin_score = 1 if vote.is_accurate else -1
                rep_fractions[vote.user_id] += self.trust_db.get_correlation_coefficient(self.identifier, vote.user_id) * bin_score
                num_votes_per_user[vote.user_id] += 1

            # Normalize the personal scores
            for user_id in rep_fractions.keys():
                rep_fractions[user_id] /= num_votes_per_user[user_id]

            # Compute the weighted average of these personal scores (the weight is the fraction in the max flow computation)
            fsum = 0
            reputation_score = 0
            for user_id in rep_fractions.keys():
                flow = self.trust_db.max_flows[user_id]
                reputation_score += flow * rep_fractions[user_id]
                fsum += flow

            rule.reputation_score = reputation_score / fsum

    def __str__(self):
        user_status = "honest" if self.type == UserType.HONEST else "adversarial"
        return "User %s (%s)" % (self.identifier, user_status)
