from enum import Enum
from random import Random


class RuleType(Enum):
    ACCURATE = 0  # An "accurate" rule is a rule created by a user with honest intentions (but can have some errors).
    SPAM = 1      # A spam rule is a rule that creates an inaccurate tag on all content it can find.


class Rule:

    def __init__(self, rule_id, output_tag, coverage=1, error_rate=0, rule_type=RuleType.ACCURATE):
        self.rule_id = rule_id
        self.output_tag = output_tag
        self.reputation_score = 0
        self.coverage = coverage
        self.error_rate = error_rate
        self.applicable_content_ids_correct = []
        self.applicable_content_ids_incorrect = []
        self.type = rule_type

    def determine_applicable_content(self, total_num_items):
        content_ids = list(range(total_num_items))
        rand = Random(hash(self))
        items_to_sample = int(self.coverage * total_num_items)
        applicable_content_ids = sorted(rand.sample(content_ids, items_to_sample))

        # Some of these content IDs should be incorrect - determine which ones
        incorrect_items_to_sample = int(self.error_rate * len(applicable_content_ids))
        incorrect_content_ids = rand.sample(applicable_content_ids, incorrect_items_to_sample)

        for content_id in applicable_content_ids:
            if content_id in incorrect_content_ids:
                self.applicable_content_ids_incorrect.append(content_id)
            else:
                self.applicable_content_ids_correct.append(content_id)

        print("Rule %s applies to: %s (correct), %s (incorrect)" % (
            hash(self), self.applicable_content_ids_correct, self.applicable_content_ids_incorrect))

    def get_copy(self):
        r = Rule(self.rule_id, self.output_tag, self.coverage)
        r.applicable_content_ids_correct = self.applicable_content_ids_correct
        r.applicable_content_ids_incorrect = self.applicable_content_ids_incorrect
        r.type = self.type
        return r

    def __hash__(self):
        return self.rule_id
