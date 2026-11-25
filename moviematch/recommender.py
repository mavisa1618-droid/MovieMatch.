"""Project 2: MovieMatch: recommender.py

This module looks up movies by title and returns
the top 5 most similar movie recommendations using the weighted graph.

Copyright (c) 2026 <Capucine, Mavi, Syaikha, Tamima>
"""
from __future__ import annotations

from moviematch.data_loader import Movie
from moviematch.graph import WeightedGraph


def title_to_id(movies: dict[int, Movie]) -> dict[str, int]:
    """Return a mapping of movie title to movie_id for all movies.

    This is used by the search bar in interface.py to look up a movie ID
    from a title given by the user.

    Preconditions:
        - len(movies) > 0

    >>> from moviematch.data_loader import Movie
    >>> m1 = Movie(1, 'Toy Story (1995)')
    >>> m2 = Movie(2, 'Jumanji (1995)')
    >>> title_to_id({1: m1, 2: m2})
    {'Toy Story (1995)': 1, 'Jumanji (1995)': 2}
    """
    return {movie.title: movie_id for movie_id, movie in movies.items()}


def recommend(title: str, graph: WeightedGraph, movies: dict[int, Movie]) -> list[tuple[Movie, float]]:
    """Return the top 5 most similar movies to the given title as a list of
    (Movie, similarity_score) tuples, sorted by similarity from highest to lowest.

    Returns an empty list if the title is not found in movies or if the movie
    has no neighbours in the graph.

    Preconditions:
        - len(movies) > 0

    >>> from moviematch.data_loader import Movie
    >>> from moviematch.graph import WeightedGraph, build_from_movies
    >>> m1 = Movie(1, 'Toy Story (1995)')
    >>> m1.genres = {'Animation', 'Comedy'}
    >>> movies = {1: m1}
    >>> g = build_from_movies(movies)
    >>> recommend('Toy Story (1995)', g, movies)
    []
    """
    title_map = title_to_id(movies)

    if title not in title_map:
        return []

    movie_id = title_map[title]
    neighbours = graph.get_neighbours(movie_id)

    return neighbours[:5]


def _get_expanded_neighbours(movie_id: int, graph: WeightedGraph,
                             movies: dict[int, Movie]) -> list[tuple[Movie, float]]:
    """Return all direct and indirect neighbours sorted by similarity.

    Indirect similarity is the product of the two scores.
    Keeps the highest score always.
    """
    seen: dict[int, float] = {}
    direct = graph.get_neighbours(movie_id)

    for movie, score in direct:
        seen[movie.movie_id] = score

    for movie, score in direct:
        for neighbour, neighbour_score in graph.get_neighbours(movie.movie_id):
            if neighbour.movie_id == movie_id:
                continue
            indirect = score * neighbour_score
            if neighbour.movie_id not in seen or seen[neighbour.movie_id] < indirect:
                seen[neighbour.movie_id] = indirect

    return sorted(
        [(movies[mid], s) for mid, s in seen.items() if mid in movies],
        key=lambda x: x[1], reverse=True
    )


def recommend_with_min_rating(title: str, graph: WeightedGraph,
                              movies: dict[int, Movie],
                              min_rating: float) -> list[tuple[Movie, float]]:
    """Return at most 5 movie recommendations whose average rating is at least min_rating.

    Searches direct neighbours and neighbours of neighbours for qualifying movies.
    If no movies have at least min_rating, returns an empty list.

    Preconditions:
        - len(movies) > 0
        - 0.0 <= min_rating <= 5.0
    """
    title_map = title_to_id(movies)

    if title not in title_map:
        return []

    movie_id = title_map[title]
    all_candidates = _get_expanded_neighbours(movie_id, graph, movies)

    qualifying = [(m, s) for m, s in all_candidates if m.avg_rating >= min_rating]

    if not qualifying:
        return []

    return qualifying[:5]


def find_bridge(title1: str, title2: str, graph: WeightedGraph,
                movies: dict[int, Movie]) -> list[Movie]:
    """Return the chain of movies that connects title1 to title2 in the graph.

    The returned list starts with title1 and ends with title2. The movies in
    between are the "bridge" between the two tastes.

    If the two movies are directly connected, there is nothing in between, so the
    best movie that is similar to BOTH of them is put in the middle instead
    (if there is one). Returns an empty list if a title is not found or the
    movies are not connected at all.

    Preconditions:
        - len(movies) > 0
    """
    title_map = title_to_id(movies)
    if title1 not in title_map or title2 not in title_map or title1 == title2:
        return []

    id1 = title_map[title1]
    id2 = title_map[title2]
    path = graph.shortest_path(id1, id2)

    if len(path) == 2:
        scores1 = {movie.movie_id: score for movie, score in graph.get_neighbours(id1)}
        best_movie = None
        best_score = 0.0
        for movie, score in graph.get_neighbours(id2):
            if movie.movie_id in scores1 and movie.movie_id != id1:
                combined = min(score, scores1[movie.movie_id])
                if combined > best_score:
                    best_movie = movie
                    best_score = combined
        if best_movie is not None:
            path = [path[0], best_movie, path[1]]

    return path


if __name__ == '__main__':
    import doctest

    doctest.testmod()

    import python_ta

    python_ta.check_all(config={
        'extra-imports': ['moviematch.data_loader', 'moviematch.graph'],
        'max-line-length': 120,
    })
