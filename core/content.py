from core.tag import Tag


class Content:

    def __init__(self, name, popularity):
        self.name = name
        self.popularity = popularity
        self.tags = []

    def get_tag_with_name(self, tag_str):
        for tag in self.tags:
            if tag.name == tag_str:
                return tag
        return None

    def apply_rule(self, rule):
        if hash(self) not in rule.applicable_content_ids_correct and hash(self) not in rule.applicable_content_ids_incorrect:
            return

        tag = self.get_tag_with_name(rule.output_tag)
        if not tag:
            tag = Tag(rule.output_tag, hash(self))
            self.tags.append(tag)
        tag.rules.append(hash(rule))

    def __hash__(self):
        return int(self.name)
