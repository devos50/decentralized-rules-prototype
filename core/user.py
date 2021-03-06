import random
from asyncio import sleep
from enum import Enum
from typing import List

from numpy import average

from core.content import Content
from core.db.content_database import ContentDatabase
from core.db.peers_database import PeersDatabase
from core.db.rules_database import RulesDatabase
from core.db.tags_database import TagsDatabase
from core.db.trust_database import TrustDatabase
from core.db.votes_database import VotesDatabase
from core.exchange import RandomExchangePolicy
from core.tag import Tag
from core.vote import Vote


class UserType(Enum):
    HONEST = "honest"
    CREATE_INACCURATE_TAGS = "bad_tagger"
    NAIVE_NEGATIVE_VOTER = "naive_downvote"
    NAIVE_POSITIVE_VOTER = "naive_upvote"
    NAIVE_RANDOM_VOTER = "naive_randvote"
    FIXED_NAIVE_NEGATIVE_VOTER = "fixed_naive_downvote"
    FIXED_NAIVE_POSITIVE_VOTER = "fixed_naive_upvote"
    FIXED_NAIVE_RANDOM_VOTER = "fixed_naive_randvote"
    LOWER_REPUTATION = "lower_reputation"


class User:

    def __init__(self, identifier, user_type=UserType.HONEST):
        self.identifier = identifier
        self.peers_db = PeersDatabase()
        self.rules_db = RulesDatabase()
        self.tags_db: TagsDatabase = TagsDatabase(self.rules_db)
        self.content_db = ContentDatabase(self.tags_db)
        self.votes_db: VotesDatabase = VotesDatabase(hash(self))
        self.trust_db = TrustDatabase(hash(self), self.votes_db, self.tags_db)
        self.neighbours: List[User] = []
        self.type = user_type
        self.vote_exchange_policy = RandomExchangePolicy(self.votes_db)

    def connect(self, other_user):
        self.neighbours.append(other_user)
        self.peers_db.add_peer(hash(other_user))

    async def start_vote_exchange(self, exchange_interval, gossip_batch_size):
        while True:
            # Exchange random votes with one neighbour
            neighbour = random.choice(self.neighbours)
            votes = self.vote_exchange_policy.get_votes(hash(neighbour))
            #print("%s exchanging %d vote(s) with %s" % (self, len(votes), neighbour))
            for vote in votes:
                neighbour.process_incoming_vote(vote)
            await sleep(exchange_interval)

    def process_incoming_vote(self, vote: Vote):
        content_item = self.content_db.get_content(vote.cid)
        if not content_item:
            # It looks like this content doesn't exist in the user database - create it
            content_item = Content(str(vote.cid), 1)
            self.content_db.add_content(content_item)

        tag = content_item.get_tag_with_name(vote.tag)
        if not tag:
            # It looks like this tag does not exist yet - create it
            tag = Tag(vote.tag, vote.cid)
            self.tags_db.add_tag(tag)
            content_item.add_tag(tag)

        for author in vote.authors:
            tag.authors.add(author)  # We assume that the tag author information in the vote is reliable
        self.votes_db.add_vote(vote)

        if self.type == UserType.NAIVE_POSITIVE_VOTER or self.type == UserType.NAIVE_NEGATIVE_VOTER or self.type == UserType.NAIVE_RANDOM_VOTER:
            # We have received a vote from another user - respond to it if we are a naive vote attacker.
            if not self.votes_db.user_did_vote_for_tag(hash(self), vote.cid, vote.tag):
                if self.type == UserType.NAIVE_NEGATIVE_VOTER:
                    to_vote = False
                elif self.type == UserType.NAIVE_POSITIVE_VOTER:
                    to_vote = True
                else:
                    to_vote = random.random() < 0.5

                self.vote(tag, to_vote)

    def create_tag(self, content_id: int, tag_name: str) -> Tag:
        """
        Have this user create a particular tag.
        """
        content_item = self.content_db.get_content(content_id)
        if not content_item:
            # It looks like this content doesn't exist in the user database - create it
            content_item = Content(str(content_id), 1)
            self.content_db.add_content(content_item)

        tag = Tag(tag_name, content_id)
        tag.authors.add(hash(self))
        self.tags_db.add_tag(tag)
        content_item.add_tag(tag)

        return tag

    def vote(self, tag: Tag, is_accurate: bool) -> None:
        """
        Vote for a particular tag.
        :param tag: The tag being voted on.
        :param is_accurate: Whether the vote is positive or negative.
        """
        by_user = hash(self)

        # Recompute reputations
        self.recompute_reputations()

        linked_votes = self.trust_db.select_vote_dag_tips()
        vote = Vote(by_user, tag.cid, tag.name, is_accurate, tag.authors, tag.rules, linked_votes)
        self.votes_db.add_vote(vote)
        print("%s voted %d for %s" % (self, 1 if is_accurate else -1, tag.name))

    def apply_rules_to_content(self):
        for rule in self.rules_db.get_all_rules():
            created_tags = self.content_db.apply_rule(rule)

            # The author of the rule always upvotes the generated tags (used to compute similarity).
            for tag in created_tags:
                self.vote(tag, True, by_user=rule.author, virtual=True)

    def recompute_reputations(self):
        """
        (re)compute the reputation of users, tags, and rules.
        """
        #print("Recomputing all reputations for %s" % self)

        # Compute similarities
        self.trust_db.compute_similarities()

        # Compute max flows between pairs
        self.trust_db.compute_flows()

        # Compute the reputations of tags
        self.compute_tags_reputation()

        # Compute the reputation of rules
        self.compute_rules_reputation()

        # Compute the reputations of other users (based on their tag history)
        self.compute_user_reputation()

        # Finally, we assign a weight to each tag, depending on the reputation score of the rules and authors
        # that generated/created it
        self.compute_tag_weights()

    def compute_tags_reputation(self):
        """
        Compute the reputation of all tags, which depends on the votes cast on that tag.
        Note that this is not the final weight of the tag.
        """
        for content in self.content_db.get_all_content():
            for tag in content.tags:
                self.compute_tag_reputation(tag)

    def compute_user_reputation(self):
        """
        Compute the subjective reputation of other users.
        """
        self.trust_db.user_reputations = {hash(self): 1}
        for user_id in self.peers_db.get_peers():
            #print("Computing reputation of user %d" % user_id)

            # This will also include tags generated by a rule created by the user
            tag_reps = [tag.reputation_score for tag in self.tags_db.get_tags_created_by_user(user_id)]
            transient_similarity_score = self.trust_db.max_flows[user_id] if user_id in self.trust_db.max_flows else 0
            if not tag_reps:
                self.trust_db.user_reputations[user_id] = transient_similarity_score
            else:
                #print("Avg of tag reputation: %f" % average(tag_reps))
                self.trust_db.user_reputations[user_id] = (average(tag_reps) + transient_similarity_score) / 2

    def compute_tag_reputation(self, tag: Tag):
        """
        Compute the reputation of a particular tag.
        """
        scores = []
        votes_for_tag = self.votes_db.get_votes_for_tag(hash(tag))
        #print("Computing reputation of tag %s (votes: %d)" % (tag, len(votes_for_tag)))
        for vote in votes_for_tag:
            if vote.user_id not in self.trust_db.max_flows:
                continue

            transient_similarity = self.trust_db.max_flows[vote.user_id]
            if -0.2 < transient_similarity < 0.2:
                continue

            scores.append(transient_similarity * (1 if vote.is_accurate else -1))

        tag.reputation_score = average(scores) if scores else 0

    def compute_rules_reputation(self):
        # Compute rule reputations
        for rule in self.rules_db.get_all_rules():
            votes = {}
            print("Computing reputation for rule %d" % rule.rule_id)

            tags_for_rule = self.tags_db.get_tags_generated_by_rule(rule)
            votes_for_rule = []
            for tag in tags_for_rule:
                votes_for_rule += self.votes_db.get_votes_for_tag(hash(tag))

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
                similarity = self.trust_db.get_similarity_coefficient(hash(self), user_id)
                if -0.2 < similarity < 0.2:
                    continue
                print("Opinion of user %s on rule %s: %f (votes: %d, weight: %f, similarity: %f)" % (user_id, rule.rule_id, average(user_votes), len(user_votes), self.trust_db.max_flows[user_id], similarity))
                rep_fractions[user_id] = similarity * average(user_votes)

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

                for author in tag.authors:
                    author_rep = self.trust_db.user_reputations[author]
                    weight += author_rep
                    count += 1

                if count > 0:
                    tag.weight = (tag.reputation_score + (weight / count)) / 2

    def __str__(self):
        return "User %s (%s)" % (hash(self), self.type.value)

    def __hash__(self):
        return int(self.identifier)
