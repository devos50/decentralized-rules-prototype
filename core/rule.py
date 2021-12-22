from random import Random


class Rule:

    def __init__(self, output_tag, coverage=1):
        """
        Create a rule.
        :param output_tag: The output tag that this rule applies to content.
        :param coverage: The coverage of the rule, which is a value between 0 and 1. Indicates the fraction to which
        the rule applies to content.
        """
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

    def __hash__(self):
        return hash(self.output_tag)
