# MovieMatch

[![tests](../../actions/workflows/tests.yml/badge.svg)](../../actions/workflows/tests.yml)

Every streaming service has a "because you watched..." row, and it is usually a list of whatever is popular this week. We wanted to build one that could explain itself. MovieMatch treats 2,269 films as a graph: two movies are connected when they share genres, tags, and, most importantly, **the same people loving both of them**.

<!-- screenshot: docs/images/app.png -->

## What it does

Type a movie you like and MovieMatch gives you five others, each with a short reason (shown here for the top suggestion):

| You liked | MovieMatch suggests | Why |
|---|---|---|
| Spirited Away | My Neighbor Totoro, Castle in the Sky, Kiki's Delivery Service | Shared: Animation, Fantasy, #anime |
| The Shawshank Redemption | The Green Mile, The Godfather, American History X | Shared: Crime, Drama, #stephen king |
| Mean Girls | Ferris Bueller's Day Off, Napoleon Dynamite, Heathers | Shared: Comedy, #high school |

**Bridge mode.** Add a friend's favourite too, and MovieMatch walks the graph from your movie to theirs and suggests the film halfway between:

| You like | Your friend likes | Watch together |
|---|---|---|
| Toy Story | The Matrix | The Lord of the Rings: The Return of the King |
| Mean Girls | The Dark Knight | The Godfather |
| Titanic | Alien | The Sixth Sense |

You can also open an interactive map of the 100 movies closest to the one you searched.

## The look

The design is borrowed from the video rental stores of the 90s and early 2000s. Before streaming, picking a movie meant walking the aisles with a friend, reading the spines of the tapes, and arguing until you found something you both wanted. That's the feeling I wanted the app to have, especially bridge mode, which is basically that argument solved by a graph.

- **Colours.** Cobalt blue walls and marigold signs, the colours a lot of rental stores used so you could spot them from the street.
- **Results as tapes.** Each recommendation is drawn like a VHS case on a shelf: a white box with a thick outline and a coloured spine down the left side, so a list of results looks like a row of tapes.
- **Type.** Futura for the title and movie names, because its bold geometric letters look like old shop signs and box art, and Avenir Next for everything else so it stays easy to read.
- **Plain shapes.** No gradients, shadows or rounded corners, just flat colour and outlines, like printed signs and stickers.

## How it works

Each movie gets a similarity score with every other movie, made of three parts:

| Part | Weight | What is compared |
|---|---|---|
| Audience | 50% | People who rated both movies 4 stars or higher |
| Tags | 30% | User tags like `pixar`, `mind-bending`, `twist ending` |
| Genres | 20% | Animation, Thriller, Sci-Fi, ... |

Each part is a [Jaccard index](https://en.wikipedia.org/wiki/Jaccard_index): the size of the overlap divided by the size of the combined set. Movies scoring at least 0.2 are connected, which gives 58,656 edges.

Raw scores turned out to be confusing to show. A great match might only score 0.39, which looks like "39%". So the app shows how rare a match is instead: 0.39 is stronger than 99.98% of all 2.5 million movie pairs, so it appears as **Top 0.02%**.

Bridge mode uses breadth-first search to find the shortest chain of connected movies between two films, and picks the one in the middle. If the two movies are already directly connected, it picks the movie that is most similar to both.

## Running it

You need Python 3.10 or newer (Tkinter comes with the standard installer from python.org).

```bash
git clone https://github.com/mavisa1618-droid/MovieMatch.git
cd MovieMatch
pip install -r requirements.txt
python main.py
```

It takes about 5 seconds to build the graph before the window opens.

To run the tests and the linter:

```bash
pip install -r requirements-dev.txt
pytest
ruff check .
```

These also run on GitHub Actions on every push.

## Code layout

```
main.py                    loads the data, builds the graph, opens the app
moviematch/
    data_loader.py         reads the MovieLens CSV files and cleans up titles
    graph.py               the weighted graph, similarity scores, shortest path
    recommender.py         top 5 recommendations, rating filter, bridge mode
    interface.py           the Tkinter app
    visualisations.py      the interactive Plotly map
tests/                     pytest tests
data/                      MovieLens ml-latest-small dataset
docs/project_report.tex    our original project report
```

## Background

MovieMatch started as our final project for CSC111 (Foundations of Computer Science II) at the University of Toronto in March 2026. The original team repository is [syaikhafaizaarifin99/Project-2-CSC111](https://github.com/syaikhafaizaarifin99/Project-2-CSC111).

| Name | GitHub |
|---|---|
| Mavi Ramos Sanchez | [@mavisa1618-droid](https://github.com/mavisa1618-droid) |
| Syaikha Faiza Arifin | [@syaikhafaizaarifin99](https://github.com/syaikhafaizaarifin99) |
| Capucine Crouzet | [@crouzetc12](https://github.com/crouzetc12) |
| Tamima Wadageri | [@tamiw10](https://github.com/tamiw10) |

**My contributions:** <!-- TODO: describe your own part of the original project -->

### Updates since the course

After the course ended, I kept working on it in November 2026:

- added bridge mode
- replaced the raw similarity percentages with "Top x%" ranks
- redesigned the interface
- reorganised the code into a package and added tests, linting and CI

## Data

Ratings, tags and titles come from the [MovieLens](https://grouplens.org/datasets/movielens/) `ml-latest-small` dataset by GroupLens Research (100,836 ratings from 610 users), used under its [license](data/README.md) for non-commercial purposes.

> F. Maxwell Harper and Joseph A. Konstan. 2015. The MovieLens Datasets: History and Context. ACM Transactions on Interactive Intelligent Systems 5, 4: 19:1-19:19. https://doi.org/10.1145/2827872
