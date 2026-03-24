from __future__ import annotations
from movie import Movie


GENRE_WEIGHT = 0.6
TAG_WEIGHT = 0.4
SIMILARITY_THRESHOLD = 0.3


def jaccard_similarity(set1: set[str], set2: set[str]) -> float:
    """Return the Jaccard similarity between two sets."""
    if not set1 and not set2:
        return 0.0

    union = set1 | set2
    intersection = set1 & set2

    if len(union) == 0:
        return 0.0

    return len(intersection) / len(union)


def movie_similarity(movie1: Movie, movie2: Movie) -> float:
    """Return the weighted similarity score between two movies."""
    genre_score = jaccard_similarity(movie1.genres, movie2.genres)
    tag_score = jaccard_similarity(movie1.tags, movie2.tags)

    return GENRE_WEIGHT * genre_score + TAG_WEIGHT * tag_score
