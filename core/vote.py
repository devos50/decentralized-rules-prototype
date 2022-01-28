class Vote:

    def __init__(self, user_id: int, cid, tag, is_accurate, authors, rules_ids):
        self.user_id: int = user_id
        self.cid = cid
        self.tag = tag
        self.is_accurate = is_accurate
        self.authors = authors
        self.rules_ids = rules_ids

    def __str__(self):
        return "Vote(user %s, cid %s)" % (self.user_id, self.cid)
