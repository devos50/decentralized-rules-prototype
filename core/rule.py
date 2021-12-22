from random import Random


class Rule:

    def __init__(self, rule_id, output_tag, coverage=1):
        self.rule_id = rule_id
        self.output_tag = output_tag
        self.reputation_score = 0
        self.coverage = coverage
        self.applicable_content_ids = []

    def determine_applicable_content(self, total_num_items):
        content_ids = list(range(total_num_items))
        rand = Random(hash(self))
        items_to_sample = int(self.coverage * total_num_items)
        self.applicable_content_ids = sorted(rand.sample(content_ids, items_to_sample))
        print("Rule %s applies to: %s" % (hash(self), self.applicable_content_ids))

    def get_copy(self):
        r = Rule(self.rule_id, self.output_tag, self.coverage)
        r.applicable_content_ids = self.applicable_content_ids
        return r

    def __hash__(self):
        return self.rule_id
