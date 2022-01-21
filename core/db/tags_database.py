from typing import List

from core.tag import Tag


class TagsDatabase:
    """
    Stores the tags that a user has locally.
    """

    def __init__(self):
        self.tags = {}
        self.tags_for_content = {}  # Content ID -> List[Tag]

    def add_tag(self, tag: Tag):
        if tag.cid not in self.tags_for_content:
            self.tags_for_content[tag.cid] = []
        self.tags_for_content[tag.cid].append(tag)
        self.tags[hash(tag)] = tag

    def get_tag(self, tag_id):
        return self.tags.get(tag_id, None)

    def get_tags_created_by_user(self, user_id: int) -> List[Tag]:
        return [tag for tag in self.tags.values() if user_id in tag.authors]

    def get_all_tags(self):
        return list(self.tags.values())
