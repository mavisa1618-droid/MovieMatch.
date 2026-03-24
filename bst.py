from __future__ import annotations
from movie import Movie


class BSTNode:
    """A BST node storing a Movie, ordered by rating then num_ratings."""

    def __init__(self, movie: Movie) -> None:
        self.movie = movie
        self.left = None
        self.right = None

    def _key(self) -> tuple[float, int, str]:
        """Return the sorting key for this node."""
        return (self.movie.avg_rating, self.movie.num_ratings, self.movie.title)

    def insert(self, movie: Movie) -> None:
        """Insert movie into this BST."""
        new_key = (movie.avg_rating, movie.num_ratings, movie.title)

        if new_key < self._key():
            if self.left is None:
                self.left = BSTNode(movie)
            else:
                self.left.insert(movie)
        else:
            if self.right is None:
                self.right = BSTNode(movie)
            else:
                self.right.insert(movie)

    def reverse_inorder(self) -> list[Movie]:
        """Return movies in descending order."""
        result = []

        if self.right is not None:
            result.extend(self.right.reverse_inorder())

        result.append(self.movie)

        if self.left is not None:
            result.extend(self.left.reverse_inorder())

        return result
