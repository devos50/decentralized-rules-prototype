from typing import List, Dict

from numpy.random import choice

from core.content import Content
from core.tag import Tag


class ContentDatabase:

    def __init__(self, tags_db):
        self.content: Dict[int, Content] = {}
        self.tags_db = tags_db

    def add_content(self, content):
        self.content[hash(content)] = content

    def get_content(self, cid):
        return self.content[cid] if cid in self.content else None

    def get_all_content(self) -> List[Content]:
        return list(self.content.values())

    def get_random_content_item_by_popularity(self):
        popularities = [content.popularity for content in self.content.values()]
        return choice(list(self.content.values()), p=popularities)

    def apply_rule(self, rule) -> List[Tag]:
        new_tags = []
        for content_item in self.get_all_content():
            new_tag = content_item.apply_rule(rule, self.tags_db)
            if new_tag:
                new_tags.append(new_tag)
        return new_tags
