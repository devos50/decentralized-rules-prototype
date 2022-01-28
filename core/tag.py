class Tag:

    def __init__(self, name: str, cid: int) -> None:
        self.name: str = name
        self.cid: int = cid
        self.rules = []    # IDs of rules that have generated this tag
        self.authors = set()  # IDs of users that have proposed this tag
        self.reputation_score = 0
        self.weight = 0

    def __hash__(self):
        return hash((self.cid, self.name))

    def __str__(self):
        return "Tag(%s, %d, %s)" % (self.name, self.cid, self.authors)
