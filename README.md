# MovieMatch

[![tests](../../actions/workflows/tests.yml/badge.svg)](../../actions/workflows/tests.yml)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Tkinter](https://img.shields.io/badge/UI-Tkinter-informational)
![Plotly](https://img.shields.io/badge/graphs-Plotly-purple)

**A movie recommender that models 2,269 films as a weighted similarity graph and explains *why* each recommendation was made.**

Type a movie you like, pick a minimum rating, and MovieMatch returns the five most similar films. It ranks them by genres, user tags, and the audience that loved both movies. You can then open an interactive network graph to explore up to 100 related films.

<!-- Take a screenshot of the app (Cmd+Shift+4, then Space, then click the window) and save it as docs/images/app.png -->
![MovieMatch screenshot](docs/images/app.png)

---

## Features

- **Bridge mode.** Enter your favourite movie and a friend's, and MovieMatch finds the shortest chain of similar movies between them using breadth-first search, then suggests the movie in the middle to watch together.
- **Graph-based recommendations.** Every movie is a vertex. Every pair of sufficiently similar movies is joined by a weighted edge (58,656 edges in total).
- **Explainable results.** Each recommendation shows what the two movies share (for example *Shared: Animation · Comedy · #pixar*) or notes that the same audience loved both.
- **Two-hop search.** When the rating filter removes direct neighbours, MovieMatch also searches neighbours of neighbours. It scores them by the product of the two edge weights.
- **Live autocomplete.** Matching titles appear as you type. Press <kbd>↓</kbd> to move into the list and <kbd>Enter</kbd> to search.
- **Interactive network view.** A Plotly graph places similar movies closer to the centre and draws stronger links thicker.
- **Clean title handling.** MovieLens titles like `Matrix, The (1999)` are shown as `The Matrix (1999)`, including titles in other languages.

## What's new since the course

The original version (March 2026) recommended movies for one person. These features were added afterwards, in November 2026:

- **Bridge mode**: find a movie two people will both like (`WeightedGraph.shortest_path`, `find_bridge`)

## How it works

```
 movies.csv ─┐
 ratings.csv ─┼─► data_loader ──► Movie objects ──► graph ──► WeightedGraph ──► recommender ──► interface
 tags.csv ───┤     (clean +         (genres, tags,     (pairwise                (top 5, filtered    (Tkinter UI +
 links.csv ──┘      filter)          high raters)       similarity)              by min rating)      Plotly graph)
```

Similarity between two movies is a weighted mix of three [Jaccard indices](https://en.wikipedia.org/wiki/Jaccard_index):

| Signal | Weight | Compares |
|---|---|---|
| Audience | **50%** | Users who rated **both** movies 4 stars or higher |
| Tags | **30%** | Free-text tags such as `pixar`, `mind-bending`, `twist ending` |
| Genres | **20%** | Genres such as Animation, Thriller, Sci-Fi |

```
similarity(a, b) = 0.2 · J(genres) + 0.3 · J(tags) + 0.5 · J(high raters)
```

Two movies are connected when their similarity is at least **0.2**. Movies with fewer than 10 ratings are left out because they don't have enough data for reliable recommendations.

## Getting started

Requires **Python 3.10+**. Tkinter ships with the standard Python installers from python.org.

```bash
git clone https://github.com/<your-username>/MovieMatch.git
cd MovieMatch
pip install -r requirements.txt
python main.py
```

Building the graph takes about 5 seconds, then the window opens.

## Running the tests

```bash
pip install -r requirements-dev.txt
pytest          # unit tests + doctests
ruff check .    # linting
```

The same checks run automatically on every push through [GitHub Actions](.github/workflows/tests.yml) on Python 3.10, 3.12 and 3.13.

## Project structure

```
MovieMatch/
├── main.py                  # Entry point: load data → build graph → open the app
├── moviematch/
│   ├── data_loader.py       # Reads and cleans the MovieLens CSVs into Movie objects
│   ├── graph.py             # WeightedGraph and the similarity functions
│   ├── recommender.py       # Top-5 and rating-filtered recommendations (incl. 2-hop search)
│   ├── interface.py         # Tkinter desktop interface
│   └── visualisations.py    # Interactive Plotly network graph
├── tests/                   # pytest suite
├── data/                    # MovieLens "ml-latest-small" dataset (see data/README.md)
├── docs/project_report.tex  # Original written project report
├── pyproject.toml           # Project metadata, pytest and ruff settings
└── requirements*.txt
```

## Tech stack

Python · Tkinter · Plotly · pytest · ruff · GitHub Actions

## Team

Built as the final project for **CSC111 (Foundations of Computer Science II)** at the University of Toronto, March 2026.

| Name | GitHub |
|---|---|
| Mavi Ramos Sanchez | [@mavisa1618-droid](https://github.com/mavisa1618-droid) |
| Syaikha Faiza Arifin | [@syaikhafaizaarifin99](https://github.com/syaikhafaizaarifin99) |
| Capucine Crouzet | [@crouzetc12](https://github.com/crouzetc12) |
| Tamima Wadageri | [@tamiw10](https://github.com/tamiw10) |

**My contributions:** <!-- TODO: describe your own part, e.g. "Designed the recommendation algorithm and wrote recommender.py and main.py" -->

The original team repository is [syaikhafaizaarifin99/Project-2-CSC111](https://github.com/syaikhafaizaarifin99/Project-2-CSC111). This fork adds a redesigned interface, a test suite, linting and CI.

## Data and acknowledgements

Movie data comes from the [MovieLens](https://grouplens.org/datasets/movielens/) `ml-latest-small` dataset by GroupLens Research. It is used for non-commercial, educational purposes under its [license](data/README.md).

> F. Maxwell Harper and Joseph A. Konstan. 2015. The MovieLens Datasets: History and Context. *ACM Transactions on Interactive Intelligent Systems (TiiS)* 5, 4: 19:1–19:19. https://doi.org/10.1145/2827872
