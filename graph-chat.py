from __future__ import annotations
from movie import Movie
from similarity import movie_similarity, SIMILARITY_THRESHOLD


class MovieGraph:
    """A graph where vertices are movies and edges store similarity scores."""

    def __init__(self) -> None:
        self._movies = {}       # movie_id -> Movie
        self._edges = {}        # movie_id -> {neighbor_id: similarity}

    def add_movie(self, movie: Movie) -> None:
        """Add movie as a vertex if it is not already in the graph."""
        if movie.movie_id not in self._movies:
            self._movies[movie.movie_id] = movie
            self._edges[movie.movie_id] = {}

    def add_edge(self, movie1_id: int, movie2_id: int, score: float) -> None:
        """Add an undirected edge between two movies."""
        if movie1_id != movie2_id:
            self._edges[movie1_id][movie2_id] = score
            self._edges[movie2_id][movie1_id] = score

    def get_neighbors(self, movie_id: int) -> dict[int, float]:
        """Return neighbors of movie_id."""
        return self._edges[movie_id]

    def get_movie(self, movie_id: int) -> Movie:
        """Return the Movie object with the given id."""
        return self._movies[movie_id]

    def get_all_movies(self) -> list[Movie]:
        """Return all movies in the graph."""
        return list(self._movies.values())


def build_graph(movies: dict[int, Movie]) -> MovieGraph:
    """Return a similarity graph built from movies."""
    graph = MovieGraph()
    movie_list = list(movies.values())

    for movie in movie_list:
        graph.add_movie(movie)

    for i in range(len(movie_list)):
        for j in range(i + 1, len(movie_list)):
            movie1 = movie_list[i]
            movie2 = movie_list[j]

            score = movie_similarity(movie1, movie2)

            if score > SIMILARITY_THRESHOLD:
                graph.add_edge(movie1.movie_id, movie2.movie_id, score)

    return graph
