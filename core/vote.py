class Vote:

    def __init__(self, user_id, cid, tag, rules_ids, is_accurate):
        self.user_id = user_id
        self.cid = cid
        self.tag = tag
        self.rules_ids = rules_ids or []
        self.is_accurate = is_accurate

    @staticmethod
    def get_overlap(votes_a, votes_b):
        """
        Return two sets, one with common votes that are in agreement and one with common votes that conflict.
        """
        in_agreement = set()
        in_conflict = set()

        # TODO take into consideration that voting positively/negatively for the same rule AND the same tag is more significant than just voting for the rule
        for vote_a in votes_a:
            for vote_b in votes_b:
                if vote_a.tag == vote_b.tag and vote_a.cid == vote_b.cid and set(vote_a.rules_ids).intersection(set(vote_b.rules_ids)):
                    # TODO there's a bug here: the check is too struct - CID + tag do not have to match. Instead, we have to consider all pairs of votes.
                    # TODO alternatively, should we really work with a binary vector? Can we use a vector of integers with each entry the vote sum of the rule?
                    # Both votes endorse the same rule
                    if vote_a.is_accurate == vote_b.is_accurate:
                        in_agreement.add((vote_a, vote_b))
                    else:
                        in_conflict.add((vote_a, vote_b))

        return in_agreement, in_conflict

    def __str__(self):
        return "Vote(user %s, cid %s, rules: %s)" % (self.user_id, self.cid, self.rules_ids)