class Vote:

    def __init__(self, user_id, cid, tag, rules_ids, is_accurate):
        self.user_id = user_id
        self.cid = cid
        self.tag = tag
        self.rules_ids = rules_ids or []
        self.is_accurate = is_accurate

    def __str__(self):
        return "Vote(user %s, cid %s, rules: %s)" % (self.user_id, self.cid, self.rules_ids)
