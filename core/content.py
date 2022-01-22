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

    def add_tag(self, name: str, rule: Optional[Rule] = None, author_id: Optional[int] = None) -> Tag:
        """
        Add a new tag to this content.
        :param name: The name of the tag.
        :param rule: The rule that generated this tag (optional).
        :param author_id: The author that generated this tag (optional).
        :return The tag that has been added.
        """
        tag = self.get_tag_with_name(name)
        if not tag:
            tag = Tag(name, hash(self))
            self.tags.append(tag)

        # Update information regarding rules/authors
        if rule:
            tag.rules.append(hash(rule))
        if author_id:
            tag.authors.append(author_id)

        return tag

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
