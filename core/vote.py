class Vote:

    def __init__(self, user_id: int, cid: int, tag: str, is_accurate: bool, authors, rules_ids):
        self.user_id: int = user_id
        self.cid: int = cid
        self.tag: str = tag
        self.is_accurate: bool = is_accurate
        self.authors = authors
        self.rules_ids = rules_ids

    def __str__(self):
        return "Vote(user %s, cid %s)" % (self.user_id, self.cid)
