from typing import Set, Optional


class Vote:

    def __init__(self, user_id: int, cid: int, tag: str, is_accurate: bool,
                 authors: Optional[Set[int]], rules_ids: Optional[Set[int]], linked_votes: Set[int]):
        self.user_id: int = user_id
        self.cid: int = cid
        self.tag: str = tag
        self.is_accurate: bool = is_accurate
        self.authors: Set[int] = authors
        self.rules_ids: Optional[Set[int]] = rules_ids
        self.linked_votes: Optional[Set[int]] = linked_votes

    def __str__(self):
        return "Vote(user %s, cid %s, linked: %s)" % (self.user_id, self.cid, self.linked_votes)

    def __hash__(self):
        return hash((self.user_id, self.cid, self.tag))
