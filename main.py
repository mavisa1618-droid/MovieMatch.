from __future__ import annotations
import tkinter as tk
from pathlib import Path
from data_loader import build_movies_dict
from graph import build_graph
from ui import MovieApp


def main() -> None:
    """Run the movie recommender application."""
    data_folder = Path('data')

    movies = build_movies_dict(
        str(data_folder / 'movies.csv'),
        str(data_folder / 'ratings.csv'),
        str(data_folder / 'tags.csv')
    )
    graph = build_graph(movies)

    root = tk.Tk()
    MovieApp(root, graph, movies)
    root.mainloop()


if __name__ == '__main__':
    main()
