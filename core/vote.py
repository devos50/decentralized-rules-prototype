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
                if set(vote_a.rules_ids).intersection(set(vote_b.rules_ids)):
                    # Votes overlap
                    if vote_a.is_accurate == vote_b.is_accurate:
                        in_agreement.add((vote_a, vote_b))
                    else:
                        in_conflict.add((vote_a, vote_b))

        return in_agreement, in_conflict
