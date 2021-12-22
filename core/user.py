from enum import Enum

from core.content_database import ContentDatabase
from core.rules_database import RulesDatabase
from core.vote import Vote
from core.votes_database import VotesDatabase


class UserType(Enum):
    HONEST = 0
    RANDOM_VOTES = 1


class User:

    def __init__(self, identifier, user_type=UserType.HONEST):
        self.identifier = identifier
        self.content_db = ContentDatabase()
        self.rules_db = RulesDatabase()
        self.votes_db = VotesDatabase(self.identifier)
        self.neighbours = []
        self.type = user_type

    def connect(self, other_user):
        self.neighbours.append(other_user)

    def vote(self, tag, is_accurate):
        content_item = self.content_db.get_content(tag.cid)
        if not content_item:
            raise RuntimeError("Content item with ID %s not found in the database of user %s!" % (cid, self.identifier))

        vote = Vote(self.identifier, tag.cid, tag.name, tag.rules, is_accurate)
        self.votes_db.add_vote(vote)

    def apply_rules_to_content(self):
        for rule in self.rules_db.get_all_rules():
            self.content_db.apply_rule(rule)

    def recompute_reputations(self):
        # Compute correlations
        self.votes_db.compute_correlations()

        # Compute rule reputations
        for rule in self.rules_db.get_all_rules():
            reputation_score = 0
            votes_for_rule = self.votes_db.get_votes_for_rule(hash(rule))
            if not votes_for_rule:
                rule.reputation_score = 0
                continue

            for vote in votes_for_rule:
                reputation_score += self.votes_db.get_correlation_coefficient(vote.user_id)

            rule.reputation_score = reputation_score / len(votes_for_rule)

    def __str__(self):
        user_status = "honest" if self.type == UserType.HONEST else "adversarial"
        return "User %s (%s)" % (self.identifier, user_status)
