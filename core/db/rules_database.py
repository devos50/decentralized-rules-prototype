from core.rule import Rule


class RulesDatabase:

    def __init__(self):
        self.rules = {}
        self.rules_by_author = {}

    def add_rule(self, rule: Rule):
        self.rules[rule.get_name()] = rule

    def get_rule(self, rule_name):
        return self.rules[rule_name] if rule_name in self.rules else None

    def get_all_rules(self):
        return self.rules.values()
