from typing import List, Dict

from core.content import Content


class ContentDatabase:

    def __init__(self):
        self.content: Dict[bytes, Content] = {}

    def add_content(self, content: Content):
        self.content[content.get_hash()] = content

    def get_content(self, content_hash: bytes):
        return self.content[content_hash] if content_hash in self.content else None

    def get_all_content(self) -> List[Content]:
        return list(self.content.values())
