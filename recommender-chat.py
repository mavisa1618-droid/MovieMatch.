from __future__ import annotations
from movie import Movie
from graph import MovieGraph
from bst import BSTNode


MIN_NUM_RATINGS = 10
MAX_CANDIDATES = 50
TOP_N = 5


def search_movies(movies: dict[int, Movie], query: str) -> list[Movie]:
    """Return matching movies based on title search."""
    query = query.strip().lower()

    if query == '':
        return []

    exact_matches = []
    for movie in movies.values():
        if movie.title.lower() == query:
            exact_matches.append(movie)

    if exact_matches != []:
        return exact_matches

    words = query.split()
    partial_matches = []

    for movie in movies.values():
        title_lower = movie.title.lower()
        if all(word in title_lower for word in words):
            partial_matches.append(movie)

    return partial_matches


def get_candidate_movies(graph: MovieGraph, movie_id: int, min_rating: float) -> list[tuple[Movie, float]]:
    """Return candidate movies connected to the given movie."""
    neighbors = graph.get_neighbors(movie_id)
    candidates = []

    for neighbor_id, sim_score in neighbors.items():
        movie = graph.get_movie(neighbor_id)

        if movie.num_ratings >= MIN_NUM_RATINGS and movie.avg_rating >= min_rating:
            candidates.append((movie, sim_score))

    candidates.sort(key=lambda x: x[1], reverse=True)
    return candidates[:MAX_CANDIDATES]


def sort_candidates(candidates: list[tuple[Movie, float]]) -> list[Movie]:
    """Return candidate movies sorted from highest to lowest rating."""
    if candidates == []:
        return []

    root = BSTNode(candidates[0][0])

    for movie, _ in candidates[1:]:
        root.insert(movie)

    return root.reverse_inorder()


def recommend_movies(graph: MovieGraph,
                     target_movie: Movie,
                     min_rating: float) -> list[tuple[str, float, int]]:
    """Return top recommendations for a chosen movie."""
    candidates = get_candidate_movies(graph, target_movie.movie_id, min_rating)
    sorted_movies = sort_candidates(candidates)

    results = []
    for movie in sorted_movies[:TOP_N]:
        results.append((movie.title, movie.avg_rating, movie.num_ratings))

    return results
