"""Project 2: MovieMatch: data_loader.py

This module is responsible for loading and cleaning the MovieLens dataset
from four CSV files and returning a mapping of movie IDs to Movie objects.

Copyright (c) 2026 <Capucine, Mavi, Syaikha, Tamima>
"""
from __future__ import annotations
import csv


class Movie:
    """Represents a movie from the dataset and the data associated with it.

    Instance Attributes:
        - movie_id: unique movie's integer ID
        - title: the full title including the year (for instance, "Toy Story (1995)")
        - genres: set of genre strings for this movie.
        - tags: set of cleaned user-reported tag strings, in lower-case, for this movie.
        - avg_rating: mean of all user ratings for this movie, float (0.0 if there are no ratings for this movie)
        - rating_count: number of ratings that exist for this movie
        - imdb_id: IMDb indentifier string (for instance, "0114709"). May be empty.
        - high_raters: set of user IDs who rated this movie >= 4.0

    Representation Invariants:
        - movie_id > 0
        - 0.0 <= avg_rating <= 5.0
        - rating_count >= 0

        """

    movie_id: int
    title: str
    genres: set[str]
    tags: set[str]
    avg_rating: float
    rating_count: int
    imdb_id: str
    high_raters: set[int]

    def __init__(self, movie_id: int, title: str) -> None:
        self.movie_id = movie_id
        self.title = title
        self.genres = set()
        self.tags = set()
        self.avg_rating = 0.0
        self.rating_count = 0
        self.imdb_id = ""
        self.high_raters = set()


# Private Functions Below:

# MovieLens sometimes places an article after a comma in a title.
# Titles with commas for other reasons are left unchanged unless the word after the comma is one of these articles.
_WORDS_AFTER_COMMA = (
    'The', 'A', 'An', 'Le', 'La', 'Les', 'Il', 'Lo', 'Die', 'Der', 'Das', 'El', 'Los', "L'",
)


def _index_where_first_paren(text: str, start: int) -> int:
    """Return the index of the first '(' at or after start, or -1 if there is none."""
    i = start

    while i < len(text):
        if text[i] == '(':
            return i
        i = i + 1

    return -1


def _fix_title_order(title_segment: str) -> str:
    """If title_segment is 'Name, Word' with Word in _WORDS_AFTER_COMMA, return 'Word Name'."""
    if ', ' not in title_segment:
        return title_segment

    before_comma, after_comma = title_segment.rsplit(', ', 1)

    if after_comma in _WORDS_AFTER_COMMA:
        return after_comma + ' ' + before_comma

    return title_segment


def _find_closing_paren(text: str, open_paren_index: int) -> int:
    """Return the index just after the matching ')' for the '(' at open_paren_index.

    Preconditions:
        - 0 <= open_paren_index < len(text)
        - text[open_paren_index] == '('
        - the '(' at open_paren_index has a matching ')'
    """
    depth = 1
    scan_index = open_paren_index + 1

    while scan_index < len(text) and depth > 0:
        if text[scan_index] == '(':
            depth += 1
        elif text[scan_index] == ')':
            depth -= 1
        scan_index += 1

    return scan_index


def _fix_paren_segments(title_before_year: str) -> str:
    """Fix '..., Word' inside each (...) group (e.g. alternate-language titles).

    Parameter is the full title string with the trailing '(year)' removed.
    """
    fixed_parts = []
    index = 0

    while index < len(title_before_year):
        if title_before_year[index] == '(':
            scan_index = _find_closing_paren(title_before_year, index)
            inside_parentheses = title_before_year[index + 1:scan_index - 1]
            fixed_parts.append('(' + _fix_title_order(inside_parentheses) + ')')
            index = scan_index
        else:
            next_open_paren = _index_where_first_paren(title_before_year, index)
            if next_open_paren == -1:
                fixed_parts.append(title_before_year[index:])
                break

            fixed_parts.append(title_before_year[index:next_open_paren])
            index = next_open_paren

    return ''.join(fixed_parts)


def _normalize_movie_title(title: str) -> str:
    """Undo MovieLens 'Title, The' style when loading.

    Titles end with a space and year in parentheses, e.g. '... (1995)' (7 characters).
    """
    year_suffix = title[-7:]
    title_before_year = title[:-7]
    title_before_year = _fix_paren_segments(title_before_year)
    open_paren_index = _index_where_first_paren(title_before_year, 0)

    if open_paren_index == -1:
        return _fix_title_order(title_before_year) + year_suffix

    main_title = title_before_year[:open_paren_index]
    end = len(main_title)

    while end > 0 and main_title[end - 1] == ' ':
        end = end - 1

    main_title = main_title[:end]
    suffix_in_parentheses = title_before_year[open_paren_index:]

    return _fix_title_order(main_title) + ' ' + suffix_in_parentheses + year_suffix


def _load_movies() -> dict[int, Movie]:
    """
    Returns a mapping of movie_id to Movie object form movies.csv.

    When there are no genres listed in the csv (appears as '(no genres listed)')
    there will be an empty genres set. This means that its genre similarity is
    0.0 with all other movies.

    """
    movies = {}

    with open('movies.csv', 'r', newline='', encoding='utf-8') as movie_file:
        reader = csv.reader(movie_file)
        next(reader)
        for row in reader:
            movie_id = int(row[0])
            genres_raw = row[2]
            title = _normalize_movie_title(row[1])

            if genres_raw == '(no genres listed)':
                genres = set()
            else:
                genres = set(genres_raw.split('|'))

            movie = Movie(movie_id=movie_id, title=title)
            movie.genres = genres
            movies[movie_id] = movie

    return movies


def _load_ratings(movies: dict[int, Movie]) -> None:
    """Mutate movies, adding avg_rating and rating_count from ratings.csv

    Movies that have less than 10 ratings will have a rating_count for now, but
    they will be filtered in load_data.
    high_raters stores the set of user IDs who rated this movie >= 4.0

    """
    sum_ratings = {}
    count_ratings = {}

    with open('ratings.csv', 'r', newline='', encoding='utf-8') as ratings_file:
        reader = csv.reader(ratings_file)
        next(reader)
        for row in reader:
            movie_id = int(row[1])
            rating = float(row[2])
            sum_ratings[movie_id] = sum_ratings.get(movie_id, 0.0) + rating
            count_ratings[movie_id] = count_ratings.get(movie_id, 0) + 1
            if rating >= 4.0:
                user_id = int(row[0])
                movies[movie_id].high_raters.add(user_id)

    for movie_id, count in count_ratings.items():
        movies[movie_id].rating_count = count
        movies[movie_id].avg_rating = round(sum_ratings[movie_id] / count, 2)


def _load_tags(movies: dict[int, Movie]) -> None:
    """Mutate movies, adding movie's tags set from tags.csv.

        Tags are converted to lowercase and surrounding whitespace is stripped.
        """
    with open('tags.csv', 'r', newline='', encoding='utf-8') as tags_file:
        reader = csv.reader(tags_file)
        next(reader)
        for row in reader:
            movie_id = int(row[1])
            cleaned_tags = row[2].strip().lower()
            movies[movie_id].tags.add(cleaned_tags)


def _load_links(movies: dict[int, Movie]) -> None:
    """Mutate movies, adding the IMDb ID from links.csv.

    The imdbId column stores the numeric portion only (e.g. "0114709").
    The full URL is constructed in interface.py:
            https://www.imdb.com/title/tt{imdb_id}/
    """
    with open('links.csv', 'r', newline='', encoding='utf-8') as links_file:
        reader = csv.reader(links_file)
        next(reader)
        for row in reader:
            movie_id = int(row[0])
            movies[movie_id].imdb_id = row[1]


# Public Function

def load_data(min_ratings: int = 10) -> dict[int, Movie]:
    """Load, clean, and return all movie data as a mapping of movie_id to Movie object.

    Movies with fewer than min_ratings ratings are excluded from the returned
    dictionary because they don't have enough data for reliable recommendations.

    Preconditions:
         - min_ratings >= 0
         - movies.csv, ratings.csv, tags.csv, and links.csv are in the same
           folder as this file
    """
    movies = _load_movies()
    _load_ratings(movies)
    _load_tags(movies)
    _load_links(movies)

    rated_enough = {
        movie_id: movie
        for movie_id, movie in movies.items()
        if movie.rating_count >= min_ratings
    }

    return rated_enough


if __name__ == '__main__':
    import doctest
    doctest.testmod()

    import python_ta

    python_ta.check_all(config={
        'extra-imports': ['csv'],
        'allowed-io': [
            '_index_where_first_paren', '_fix_title_order', '_find_closing_paren', '_fix_paren_segments',
            '_normalize_movie_title', '_load_movies', '_load_ratings', '_load_tags', '_load_links'
        ],
        'max-line-length': 120,
        'max-attributes': 8,
    })
