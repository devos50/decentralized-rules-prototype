import networkx as nx
from numpy import average


class TrustDatabase:

    def __init__(self, my_id, votes_db, tags_db):
        self.my_id = my_id
        self.correlation_scores = {}
        self.max_flows = {}
        self.user_reputations = {}
        self.votes_db = votes_db
        self.tags_db = tags_db

    def compute_correlations(self):
        """
        Compute the correlation scores to all neighbours, based on the acquired local knowledge.
        """
        self.correlation_scores = {}
        for uid1 in self.votes_db.votes.keys():
            for uid2 in self.votes_db.votes.keys():
                if uid1 == uid2 and uid1 != self.my_id:
                    continue
                correlation = self.compute_correlation_coefficient(uid1, uid2)

                if uid1 not in self.correlation_scores:
                    self.correlation_scores[uid1] = {}
                if uid2 not in self.correlation_scores:
                    self.correlation_scores[uid1][uid2] = []

                self.correlation_scores[uid1][uid2] = correlation

    def get_correlation_coefficient(self, uid1, uid2):
        return self.correlation_scores[uid1][uid2] if uid1 in self.correlation_scores and uid2 in self.correlation_scores[uid1] else 0

    def compute_correlation_coefficient(self, user_a, user_b):
        """
        Compute the correlation coefficient from the perspective of this user.

        This works as follows:
        We compare all votes of both A and B.
        Votes on tags generated by a rule are grouped together, and so are votes on the same tags.
        We then take the average of all absolute differences, and take the average of these differences.
        We then subtract this final value from 1, which gives a value in the interval [-1, 1].
        """
        #print("Computing correlation between %s and %s" % (user_a, user_b))
        votes_on_rules = {}  # Rule => ([...], [...])
        votes_on_tags = {}

        for vote in self.votes_db.get_votes_for_user(user_a):
            for rule_id in vote.rules_ids:
                if rule_id not in votes_on_rules:
                    votes_on_rules[rule_id] = ([], [])
                votes_on_rules[rule_id][0].append(1 if vote.is_accurate else -1)

            tag_hash = hash((vote.cid, vote.tag))
            if tag_hash not in votes_on_tags:
                votes_on_tags[tag_hash] = ([], [])
            votes_on_tags[tag_hash][0].append(1 if vote.is_accurate else -1)

        # Tags created by user A should implicitly be upvoted
        for tag_by_a in self.tags_db.get_tags_created_by_user(int(user_a)):
            tag_hash = hash(tag_by_a)
            if tag_hash not in votes_on_tags:
                votes_on_tags[tag_hash] = ([], [])
            votes_on_tags[tag_hash][0].append(1)

        for vote in self.votes_db.get_votes_for_user(user_b):
            for rule_id in vote.rules_ids:
                if rule_id not in votes_on_rules:
                    votes_on_rules[rule_id] = ([], [])
                votes_on_rules[rule_id][1].append(1 if vote.is_accurate else -1)

            tag_hash = hash((vote.cid, vote.tag))
            if tag_hash not in votes_on_tags:
                votes_on_tags[tag_hash] = ([], [])
            votes_on_tags[tag_hash][1].append(1 if vote.is_accurate else -1)

        # Tags created by user B should implicitly be upvoted
        for tag_by_b in self.tags_db.get_tags_created_by_user(int(user_b)):
            tag_hash = hash(tag_by_b)
            if tag_hash not in votes_on_tags:
                votes_on_tags[tag_hash] = ([], [])
            votes_on_tags[tag_hash][1].append(1)

        #print("Votes between %s and %s: %s (rules) %s (tags)" % (user_a, user_b, votes_on_rules, votes_on_tags))

        diffs = []

        # For each rule, we compute the average rating by each user and compute the absolute difference.
        for rule_id, votes in votes_on_rules.items():
            votes_a, votes_b = votes
            if not votes_a or not votes_b:
                continue  # No overlap to work with

            diffs.append(abs(average(votes_a) - average(votes_b)))

        # For each tag, we compute the average rating by each user and compute the absolute difference.
        for tag_id, votes in votes_on_tags.items():
            votes_a, votes_b = votes
            if not votes_a or not votes_b:
                continue  # No overlap to work with

            diffs.append(abs(average(votes_a) - average(votes_b)))

        if not diffs:
            return 0

        return 1 - average(diffs)

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
        self.max_flows[self.my_id] = sum(self.max_flows.values()) if self.max_flows else 1
