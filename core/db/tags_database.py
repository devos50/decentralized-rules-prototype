class TagsDatabase:
    """
    Stores the tags that a user has locally.
    """

    def __init__(self):
        self.tags = []
        self.tags_for_content = {}  # Content ID -> List[Tag]

    def add_tag(self, tag):
        if tag.cid not in self.tags_for_content:
            self.tags_for_content[tag.cid] = []
        self.tags_for_content[tag.cid].append(tag)
        self.tags.append(tag)

    def get_tags(self, cid):
        return self.tags_for_content[cid] if cid in self.tags_for_content else []
