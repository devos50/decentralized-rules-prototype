from typing import Optional

from core.db.tags_database import TagsDatabase
from core.rule import Rule
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

    def add_tag(self, tag: Tag) -> None:
        """
        Add a new tag to this content.
        :param tag: The tag to add.
        """
        if tag not in self.tags:
            self.tags.append(tag)

    def apply_rule(self, rule: Rule, tags_database: TagsDatabase) -> Optional[Tag]:
        """
        Apply a rule to this content.
        :param rule: The rule to apply.
        :param tags_database: The database with tags, so we can add the new tag.
        :return: The new tag, if the rule has created one.
        """
        if hash(self) not in rule.applicable_content_ids_correct and hash(self) not in rule.applicable_content_ids_incorrect:
            return None

        tag = self.add_tag(rule.output_tag, rule=rule)
        tags_database.add_tag(tag)
        return tag

    def __hash__(self):
        # TODO this should be replaced by proper hashes
        return int(self.name)
