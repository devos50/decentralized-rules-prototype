class Tag:

    def __init__(self, name, cid):
        self.name = name
        self.cid = cid
        self.rules = []  # IDs of rules that have generated this tag
        self.weight = 0
