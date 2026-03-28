"""Project 2: MovieMatch: recommender.py

This module looks up movies by title and returns
the top 5 most similar movie recommendations using the weighted graph.

"""
from __future__ import annotations
from data_loader import Movie
from graph import WeightedGraph


def title_to_id(movies: dict[int, Movie]) -> dict[str, int]:
    """Return a mapping of movie title to movie_id for all movies.

    This is used by the search bar in interface.py to look up a movie ID
    from a title given by the user.

    Preconditions:
        - len(movies) > 0

    >>> from data_loader import Movie
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

    >>> from data_loader import Movie
    >>> from graph import WeightedGraph, build_from_movies
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
    """Returns at most 5 movie recommendations that have the minimum rating.

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
    fallback = [(m, s) for m, s in all_candidates if m.avg_rating < min_rating]

    if not qualifying:
        return []

    result = qualifying[:5]
    if len(result) < 5:
        result += fallback[:5 - len(result)]

    return result


if __name__ == '__main__':
    import doctest

    doctest.testmod()

    import python_ta

    python_ta.check_all(config={
        'extra-imports': ['data_loader', 'graph'],
        'max-line-length': 120,
    })
