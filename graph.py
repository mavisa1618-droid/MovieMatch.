"""Project 2: MovieMatch: graph.py

This module builds a weighted graph of movies where each edge represents
the similarity between two movies based on shared genres, tags, and high raters.

"""
from __future__ import annotations
from data_loader import Movie


class _Vertex:
    """Represents a movie vertex in the weighted graph.

    Instance Attributes:
        - movie: the Movie object the vertex represents
        - neighbours: a mapping of neighbouring vertices to their similarity score

    Representation Invariants:
        - self not in self.neighbours
        - all(0.0 <= score <= 1.0 for score in self.neighbours.values())
    """

    movie: Movie
    neighbours: dict[_Vertex, float]

    def __init__(self, movie: Movie) -> None:
        self.movie = movie
        self.neighbours = {}


class WeightedGraph:
    """A weighted graph where each vertex is a movie and each edge
    represents the similarity between two movies.

    Instance Attributes:
        - _vertices: a mapping of movie_id to _Vertex

    Representation Invariants:
        - all vertices in _vertices are unique movies
    """

    _vertices: dict[int, _Vertex]

    def __init__(self) -> None:
        self._vertices = {}

    def add_vertex(self, movie: Movie) -> None:
        """Add a vertex for the given movie to this graph.

        Preconditions:
            - movie.movie_id not in self._vertices
        """
        self._vertices[movie.movie_id] = _Vertex(movie)

    def add_edge(self, movie_id1: int, movie_id2: int, similarity: float) -> None:
        """Add an edge between the two vertices with the given similarity score.

        Preconditions:
            - movie_id1 in self._vertices
            - movie_id2 in self._vertices
            - movie_id1 != movie_id2
            - 0.0 <= similarity <= 1.0
        """
        vertex1 = self._vertices[movie_id1]
        vertex2 = self._vertices[movie_id2]
        vertex1.neighbours[vertex2] = similarity
        vertex2.neighbours[vertex1] = similarity

    def get_neighbours(self, movie_id: int) -> list[tuple[Movie, float]]:
        """Return a list of (Movie, similarity_score) tuples for all neighbours
        of the input movie, sorted by similarity score from highest to lowest.

        Preconditions:
            - movie_id in self._vertices
        """
        vertex = self._vertices[movie_id]
        neighbours = [
            (neighbour.movie, score)
            for neighbour, score in vertex.neighbours.items()
        ]
        return sorted(neighbours, key=lambda x: x[1], reverse=True)


def overlap_similarity(set1: set, set2: set) -> float:
    """Return the proportion of shared elements between two sets out of all
    unique elements combined. The function will return 0.0 if both sets are empty.

    This is computed as |set1 ∩ set2| / |set1 ∪ set2|, that is, the number
    of elements in common divided by the total number of unique elements
    of both sets.

    This is a helper to compute genre, tag, and user similarity between two movies
    later in combined_similarity.

    Preconditions:
        - set1 is not None
        - set2 is not None

    # doctest: intersection is {'Comedy'}, union is {'Action', 'Comedy', 'Drama'}
    # that is 1/3 = 0.3333333333333...
    >>> overlap_similarity({'Action', 'Comedy'}, {'Comedy', 'Drama'})
    0.3333333333333333
    >>> overlap_similarity(set(), set())
    0.0
    """
    if len(set1) == 0 and len(set2) == 0:
        return 0.0
    return len(set1.intersection(set2)) / len(set1.union(set2))


def combined_similarity(movie1: Movie, movie2: Movie) -> float:
    """Return the combined similarity score between two movies.

    The score is a weighted average of three components:
        - 20% genre similarity: proportion of shared genres
        - 30% tag similarity: proportion of shared user-reported tags
        - 50% user similarity: proportion of shared users who rated both movies >= 4.0

    The final score is between 0.0 and 1.0, where higher scores indicate higher similarity.

    Preconditions:
        - movie1 is not None
        - movie2 is not None
    """
    genre_score = overlap_similarity(movie1.genres, movie2.genres)
    tag_score = overlap_similarity(movie1.tags, movie2.tags)
    user_score = overlap_similarity(movie1.high_raters, movie2.high_raters)

    return round(0.2 * genre_score + 0.3 * tag_score + 0.5 * user_score, 4)


def build_from_movies(movies: dict[int, Movie]) -> WeightedGraph:
    """Build and return a WeightedGraph from the movies.

    Each movie becomes a vertex. An edge is added between two movies
    if their combined similarity score is >= 0.2.

    Preconditions:
        - len(movies) > 0
    """
    graph = WeightedGraph()

    for movie in movies.values():
        graph.add_vertex(movie)

    movie_list = list(movies.values())
    for i in range(len(movie_list)):
        for j in range(i + 1, len(movie_list)):
            movie1 = movie_list[i]
            movie2 = movie_list[j]
            score = combined_similarity(movie1, movie2)
            if score >= 0.2:
                graph.add_edge(movie1.movie_id, movie2.movie_id, score)

    return graph


if __name__ == '__main__':
    import doctest

    doctest.testmod()

    import python_ta

    python_ta.check_all(config={
        'extra-imports': ['data_loader'],
        'max-line-length': 120,
    })
