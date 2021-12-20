class RulesDatabase:

    def __init__(self):
        self.rules = {}

    def add_rule(self, rule):
        self.rules[hash(rule)] = rule

    def add_rules(self, rules):
        for rule in rules:
            self.add_rule(rule)

    def get_rule(self, rule_id):
        return self.rules[rule_id] if rule_id in self.rules else None

    def get_all_rules(self):
        return self.rules.values()
