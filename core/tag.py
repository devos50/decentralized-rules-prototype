class Tag:

    def __init__(self, name, cid):
        self.name = name
        self.cid = cid
        self.rules = []    # IDs of rules that have generated this tag
        self.authors = []  # IDs of users that have proposed this tag
        self.weight = 0
