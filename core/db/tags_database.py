from typing import List

from core.db.rules_database import RulesDatabase
from core.rule import Rule
from core.tag import Tag


class TagsDatabase:
    """
    Stores the tags that a user has locally.
    """

    def __init__(self, rules_db: RulesDatabase):
        self.rules_db = rules_db
        self.tags = {}
        self.tags_for_content = {}  # Content ID -> List[Tag]
        self.tags_by_users = {}

    def add_tag(self, tag: Tag):
        if tag.cid not in self.tags_for_content:
            self.tags_for_content[tag.cid] = []
        self.tags_for_content[tag.cid].append(tag)
        self.tags[hash(tag)] = tag

        for author in tag.authors:
            if author not in self.tags_by_users:
                self.tags_by_users[author] = set()
            self.tags_by_users[author].add(tag)

    def get_tag(self, tag_id):
        return self.tags.get(tag_id, None)

    def get_tags_created_by_user(self, user_id: int) -> List[Tag]:
        tags_by_user = list(self.tags_by_users[user_id]) if user_id in self.tags_by_users else []
        rules_by_user = self.rules_db.get_rule_ids_created_by_user(user_id)
        tags_by_user += [tag for tag in self.get_all_tags() if set(tag.rules).intersection(rules_by_user)]
        return tags_by_user

    def get_tags_generated_by_rule(self, rule: Rule) -> List[Tag]:
        return [tag for tag in self.get_all_tags() if rule.rule_id in tag.rules]

    def get_all_tags(self):
        return list(self.tags.values())
