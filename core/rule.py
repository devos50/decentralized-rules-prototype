class Rule:

    def __init__(self, output_tag):
        self.output_tag = output_tag
        self.reputation_score = 0

    def __hash__(self):
        return hash(self.output_tag)
