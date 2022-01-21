class Tag:

    def __init__(self, name, cid):
        self.name = name
        self.cid = cid
        self.rules = []    # IDs of rules that have generated this tag
        self.authors = []  # IDs of users that have proposed this tag
        self.reputation_score = 0
        self.weight = 0

    def __hash__(self):
        return hash((self.cid, self.name))
