from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class Movie:
    """A movie in the recommendation system."""
    movie_id: int
    title: str
    genres: set[str]
    tags: set[str] = field(default_factory=set)
    avg_rating: float = 0.0
    num_ratings: int = 0

    def __str__(self) -> str:
        return f'{self.title} ({self.avg_rating:.2f}, {self.num_ratings} ratings)'
