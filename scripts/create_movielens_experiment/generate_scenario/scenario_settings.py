from attr import dataclass


@dataclass
class ScenarioSettings:
    num_honest_users: int = 10
    num_bad_taggers: int = 1
    num_movies = 10
    sample_random_movies = True
    duration = 300
