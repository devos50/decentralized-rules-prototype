from typing import Set

from attr import dataclass


@dataclass
class Tag:
    movie_id: str
    tag: str
    author: int
    upvotes: Set[int]
    downvotes: Set[int]
