from typing import List

from core.rule import Rule


class RulesDatabase:

    def __init__(self):
        self.rules = {}
        self.rules_by_author = {}

    def add_rule(self, rule):
        self.rules[hash(rule)] = rule
        if rule.author not in self.rules_by_author:
            self.rules_by_author[rule.author] = []
        self.rules_by_author[rule.author].append(rule.rule_id)

    def add_rules(self, rules):
        for rule in rules:
            self.add_rule(rule)

    def get_rule(self, rule_id):
        return self.rules[rule_id] if rule_id in self.rules else None

    def get_rule_ids_created_by_user(self, user_id: int) -> List[int]:
        return self.rules_by_author[user_id] if user_id in self.rules_by_author else []

    def get_all_rules(self):
        return self.rules.values()
