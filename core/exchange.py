from typing import List

from core.db.votes_database import VotesDatabase
from core.vote import Vote


class ExchangePolicy:

    def __init__(self, votes_db: VotesDatabase) -> None:
        self.votes_db = votes_db

    def get_votes(self, target_user_id: int) -> List[Vote]:
        ...


class RandomExchangePolicy(ExchangePolicy):

    def get_votes(self, target_user_id: int) -> List[Vote]:
        return self.votes_db.get_random_votes(limit=20, exclude=target_user_id)
