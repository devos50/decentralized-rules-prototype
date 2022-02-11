from attr import dataclass


@dataclass
class ScenarioAction:
    command: str
    timestamp: float
    user_id: int
    movie_id: int
    tag: str
    is_upvote: bool
