from __future__ import annotations
import csv
from movie import Movie


def load_movies(filename: str) -> dict[int, Movie]:
    """Return a dictionary mapping movie id to Movie from movies.csv."""
    movies = {}

    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            movie_id = int(row['movieId'])
            genres_str = row['genres']

            if genres_str == '(no genres listed)':
                genres = set()
            else:
                genres = set(genres_str.split('|'))

            movies[movie_id] = Movie(
                movie_id=movie_id,
                title=row['title'],
                genres=genres
            )

    return movies


def load_ratings(filename: str) -> dict[int, list[float]]:
    """Return a dictionary mapping movie id to a list of ratings."""
    ratings = {}

    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            movie_id = int(row['movieId'])
            rating = float(row['rating'])

            if movie_id not in ratings:
                ratings[movie_id] = []

            ratings[movie_id].append(rating)

    return ratings


def load_tags(filename: str) -> dict[int, set[str]]:
    """Return a dictionary mapping movie id to a set of tags."""
    tags = {}

    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            movie_id = int(row['movieId'])
            tag = row['tag'].strip().lower()

            if movie_id not in tags:
                tags[movie_id] = set()

            if tag != '':
                tags[movie_id].add(tag)

    return tags


def build_movies_dict(movies_file: str, ratings_file: str, tags_file: str) -> dict[int, Movie]:
    """Return a dictionary mapping movie id to a complete Movie object."""
    movies = load_movies(movies_file)
    ratings_data = load_ratings(ratings_file)
    tags_data = load_tags(tags_file)

    for movie_id in movies:
        if movie_id in ratings_data:
            ratings = ratings_data[movie_id]
            movies[movie_id].avg_rating = sum(ratings) / len(ratings)
            movies[movie_id].num_ratings = len(ratings)

        if movie_id in tags_data:
            movies[movie_id].tags = tags_data[movie_id]

    return movies
