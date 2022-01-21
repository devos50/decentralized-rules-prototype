from typing import List

from core.tag import Tag


class TagsDatabase:
    """
    Stores the tags that a user has locally.
    """

    def __init__(self):
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
        return list(self.tags_by_users[user_id]) if user_id in self.tags_by_users else []

    def get_all_tags(self):
        return list(self.tags.values())
