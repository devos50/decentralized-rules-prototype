from enum import Enum
from typing import Optional

from numpy import average

from core.db.content_database import ContentDatabase
from core.db.rules_database import RulesDatabase
from core.db.tags_database import TagsDatabase
from core.db.trust_database import TrustDatabase
from core.db.votes_database import VotesDatabase
from core.tag import Tag
from core.vote import Vote


class UserType(Enum):
    HONEST = 0
    RANDOM_VOTES = 1
    PROMOTE_SPAM_RULES = 2
    TAG_SPAMMER = 3


class User:

    def __init__(self, identifier, user_type=UserType.HONEST):
        self.identifier = identifier
        self.tags_db: TagsDatabase = TagsDatabase()
        self.content_db = ContentDatabase(self.tags_db)
        self.rules_db = RulesDatabase()
        self.votes_db: VotesDatabase = VotesDatabase(self.identifier)
        self.trust_db = TrustDatabase(self.identifier, self.votes_db, self.tags_db)
        self.neighbours = []
        self.type = user_type

    def connect(self, other_user):
        self.neighbours.append(other_user)

    def vote(self, tag, is_accurate):
        content_item = self.content_db.get_content(tag.cid)
        if not content_item:
            raise RuntimeError("Content item with ID %s not found in the database of user %s!" % (tag.cid, self.identifier))

        vote = Vote(self.identifier, tag.cid, tag.name, tag.rules, is_accurate)
        self.votes_db.add_vote(vote)

    def tag(self, content_id: int, tag_name: str) -> Optional[Tag]:
        """
        Annotate some content with a tag.
        """
        content = self.content_db.get_content(content_id)
        if not content:
            return None

        print("%s tags content %s with name: %s" % (self, hash(content), tag_name))

        tag = content.add_tag(tag_name, author_id=hash(self))
        self.tags_db.add_tag(tag)
        return tag

    def apply_rules_to_content(self):
        for rule in self.rules_db.get_all_rules():
            self.content_db.apply_rule(rule)

    def recompute_reputations(self):
        """
        (re)compute the reputation of users, tags, and rules.
        """
        print("Computing scores/weights for %s" % self)

        # Compute correlations
        self.trust_db.compute_correlations()

        # Compute max flows between pairs
        self.trust_db.compute_flows()

        # Compute the reputations of tags
        self.compute_tags_reputation()

        # Compute the reputations of other users (based on their tag history)
        self.compute_user_reputation()

        # # Compute the reputation of rules
        # self.compute_rules_reputation()
        #
        # # Finally, we assign a weight to each tag, depending on the reputation score of the rules that generated it
        # self.compute_tag_weights()

    def compute_tags_reputation(self):
        """
        Compute the reputation of all tags, which depends on the votes cast on that tag.
        Note that this is not the final weight of the tag.
        """
        for content in self.content_db.get_all_content():
            for tag in content.tags:
                self.compute_tag_reputation(tag)

    def compute_user_reputation(self):
        self.trust_db.user_reputations = {}
        for user_id, tags in self.tags_db.tags_by_users.items():
            if user_id == hash(self):
                self.trust_db.user_reputations[user_id] = 1  # You fully trust yourself
                continue

            # TODO we only consider individual tags for now - we should also take rules into consideration
            tag_reps = [tag.reputation_score for tag in self.tags_db.get_tags_created_by_user(user_id)]
            self.trust_db.user_reputations[user_id] = average(tag_reps)

    def compute_tag_reputation(self, tag: Tag):
        """
        Compute the reputation of a particular tag.
        """
        rep_fractions = {}
        votes_for_tag = self.votes_db.get_votes_for_tag(hash(tag))
        for vote in votes_for_tag:
            correlation = self.trust_db.get_correlation_coefficient(self.identifier, vote.user_id)
            if -0.2 < correlation < 0.2:
                continue

            rep_fractions[vote.user_id] = correlation * (1 if vote.is_accurate else -1)

        # Compute the weighted average of these personal scores (the weight is the fraction in the max flow computation)
        fsum = 0
        reputation_score = 0
        for user_id in rep_fractions.keys():
            flow = self.trust_db.max_flows[user_id]
            reputation_score += flow * rep_fractions[user_id]
            fsum += flow

        tag.reputation_score = 0 if fsum == 0 else reputation_score / fsum

    def compute_rules_reputation(self):
        # Compute rule reputations
        for rule in self.rules_db.get_all_rules():
            votes = {}
            print("Computing reputation for rule %d" % rule.rule_id)
            votes_for_rule = self.votes_db.get_votes_for_rule(hash(rule))
            if not votes_for_rule:
                rule.reputation_score = 0
                continue

            # Collect the votes for this rule
            for vote in votes_for_rule:
                if rule.rule_id not in votes:
                    votes[rule.rule_id] = {}
                if vote.user_id not in votes[rule.rule_id]:
                    votes[rule.rule_id][vote.user_id] = []
                votes[rule.rule_id][vote.user_id].append(1 if vote.is_accurate else -1)

            rep_fractions = {}
            for user_id, user_votes in votes[rule.rule_id].items():
                correlation = self.trust_db.get_correlation_coefficient(self.identifier, user_id)
                if -0.2 < correlation < 0.2:
                    continue
                print("Opinion of user %s on rule %s: %f (votes: %d, weight: %f, correlation: %f)" % (user_id, rule.rule_id, average(user_votes), len(user_votes), self.trust_db.max_flows[user_id], correlation))
                rep_fractions[user_id] = correlation * average(user_votes)

            # Compute the weighted average of these personal scores (the weight is the fraction in the max flow computation)
            fsum = 0
            reputation_score = 0
            for user_id in rep_fractions.keys():
                flow = self.trust_db.max_flows[user_id]
                reputation_score += flow * rep_fractions[user_id]
                fsum += flow

            rule.reputation_score = 0 if fsum == 0 else reputation_score / fsum

    def compute_tag_weights(self):
        """
        Compute the weight of the tags associated with content.
        This weight is simply the average of the reputations of the rules that generated the tag.
        """
        for content in self.content_db.get_all_content():
            for tag in content.tags:
                count = 0
                weight = 0
                for rule_id in tag.rules:
                    rule_rep = self.rules_db.get_rule(rule_id).reputation_score
                    weight += rule_rep
                    count += 1
                tag.weight = weight / count

    def __str__(self):
        user_status = "honest" if self.type == UserType.HONEST else "adversarial"
        return "User %s (%s)" % (self.identifier, user_status)

    def __hash__(self):
        return int(self.identifier)