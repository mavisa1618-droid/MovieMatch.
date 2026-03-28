"""Project 2: MovieMatch: main.py

Here MovieMatch runs.
It loads the data and builds the graph and the interface.

Copyright (c) 2026 <Capucine, Mavi, Syaikha, Tamima>
"""
from data_loader import load_data
from graph import build_from_movies
from interface import run_app

if __name__ == '__main__':
    print('Loading data...')
    movies = load_data()
    print('Building graph...')
    graph = build_from_movies(movies)
    print('Launching MovieMatch...')
    run_app(movies, graph)
