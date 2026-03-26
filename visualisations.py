"""Project 2: MovieMatch: visualisations.py

This module creates an interactive network graph that appears at the bottom of the MovieMatch
interface. When a user searches for a movie, 100 similar movies are
arranged around the input movie. Distance from the centre and line thickness reflect similarity: closer
and thicker means more similar. Top 5 recommendations always show labels. All other movies show
info on hover only. The user can zoom and pan to explore.

Implementation inspired by:
- https://plotly.com/python/network-graphs/
- https://github.com/Ashton-Sidhu/plotly-graph

"""
from __future__ import annotations
import math
import plotly.graph_objects as go
from data_loader import Movie
from graph import WeightedGraph


def _get_hundred_movies(movie_id: int, graph: WeightedGraph,
                        movies: dict[int, Movie]) -> list[tuple[Movie, float]]:
    """Return up to 100 movies most similar to the input movie.

    Includes direct neighbours and neighbours of neighbours.

    Indirect similarity is the product of the two edge weights.
    (score of direct neighbour to input * score of indirect to direct neighbour)
    If the same indirect neighbour appears through different paths we use the highest score.
    """
    seen = {}  # int to float, neighbour movie_id to score

    direct = graph.get_neighbours(movie_id)
    for movie, score in direct:
        seen[movie.movie_id] = score

    for movie, score in direct:
        for neighbour, neighbour_score in graph.get_neighbours(movie.movie_id):
            if neighbour.movie_id == movie_id:
                continue
            indirect_score = score * neighbour_score
            if neighbour.movie_id not in seen or seen[neighbour.movie_id] < indirect_score:
                seen[neighbour.movie_id] = indirect_score

    sorted_by_score = sorted(seen.items(), key=lambda x: x[1], reverse=True)[:100]
    return [(movies[mov_id], final_score) for mov_id, final_score in sorted_by_score]


def _compute_positions(hundred_movies: list[tuple[Movie, float]]) -> list[tuple[float, float]]:
    """Return (x, y) positions for each movie.

    Distance from the centre reflects similarity, that is, more similar movies are
    placed closer.

    - (1.0 / score) means higher similarity will have smaller radius (close to input)
    - (-0.7) makes sure no movie is exacly on input

    We use golden ratio to make the angle of each node to input
    spread circularly around the input without overlapping.
    """
    positions = []
    for i, (_, score) in enumerate(hundred_movies):
        radius = (1.0 / score) - 0.7
        angle = i * 2.399
        positions.append((radius * math.cos(angle), radius * math.sin(angle)))
    return positions


def _build_edge_traces(hundred_movies: list[tuple[Movie, float]],
                       top5_ids: set[int],
                       positions: list[tuple[float, float]]) -> list[go.Scatter]:
    """Return lines from the input movie at centre to each neighbour.

    Top 5 get blue lines, others get faded lines.
    """
    edge_traces = []
    for i, (movie, score) in enumerate(hundred_movies):
        x, y = positions[i]

        if movie.movie_id in top5_ids:
            color = '#60A5FA'
            width = (score ** 2) * 12
        else:
            color = '#1e1e35'
            width = max(0.3, score * 3)  # so line doesn't dissapear

        edge_traces.append(go.Scatter(
            x=[0, x, None],
            y=[0, y, None],
            mode='lines',
            line={'width': width, 'color': color},
            hoverinfo='none',
            showlegend=False
        ))
    return edge_traces


def _build_top5_trace(hundred_movies: list[tuple[Movie, float]],
                      top5_ids: set[int],
                      positions: list[tuple[float, float]]) -> go.Scatter:
    """Return the trace for top 5 nodes, always show labels instead of hover.

         - (f'{movie.title}<br>★ {movie.avg_rating}<br>{round(score * 100)}%') so that
         label shows, for instance:
                Toy Story 2 (1999)
                ★ 3.86
                51%
         - (+10) for node_size so that no node is too small to see.
    """

    node_x, node_y, node_text, node_size = [], [], [], []

    for i, (movie, score) in enumerate(hundred_movies):
        if movie.movie_id not in top5_ids:
            continue

        x, y = positions[i]
        node_x.append(x)
        node_y.append(y)

        node_text.append(f'{movie.title}<br>★ {movie.avg_rating}<br>{round(score * 100)}%')
        node_size.append((movie.avg_rating ** 2) * 5 + 10)

    return go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        text=node_text,
        textposition='middle center',
        textfont={'color': 'white', 'size': 9},
        marker={'size': node_size, 'color': '#12121f',
                'line': {'width': 2.5, 'color': '#4F46E5'}},
        hoverinfo='none',
        showlegend=False
    )


def _build_other_trace(hundred_movies: list[tuple[Movie, float]],
                       top5_ids: set[int],
                       positions: list[tuple[float, float]]) -> go.Scatter:
    """Return the trace for non-top-5 nodes, shows label on hover only.
        - hoverinfo='text': so that label appears when cursor is on node.
        - (f'{movie.title}<br>★ {movie.avg_rating}<br>{round(score * 100)}%') so that
        label shows, for instance:
                Toy Story 2 (1999)
                ★ 3.86
                51%
        - (+5) for node_size so that no node is too small to see.
                """
    node_x, node_y, hover_text, node_size = [], [], [], []
    for i, (movie, score) in enumerate(hundred_movies):
        if movie.movie_id in top5_ids:
            continue

        x, y = positions[i]
        node_x.append(x)
        node_y.append(y)

        hover_text.append(f'{movie.title}<br>★ {movie.avg_rating}<br>{round(score * 100)}%')
        node_size.append((movie.avg_rating ** 2) * 3 + 5)

    return go.Scatter(
        x=node_x, y=node_y,
        mode='markers',
        marker={'size': node_size, 'color': '#12121f',
                'line': {'width': 1.0, 'color': '#2a2a4a'}},
        hovertext=hover_text,
        hoverinfo='text',
        hoverlabel={'bgcolor': '#12121f', 'font': {'color': 'white', 'size': 11},
                    'bordercolor': '#4F46E5'},
        showlegend=False
    )


def _build_input_trace(input_movie: Movie) -> go.Scatter:
    """Return the trace for the input movie node at the centre.
        - size is always biggest ([(input_movie.avg_rating ** 2) * 6 + 20])
    """
    return go.Scatter(
        x=[0.0], y=[0.0],
        mode='markers+text',
        text=[f'{input_movie.title}<br>★ {input_movie.avg_rating}'],
        textposition='top center',
        textfont={'color': '#A78BFA', 'size': 10},
        marker={'size': [(input_movie.avg_rating ** 2) * 6 + 20],
                'color': '#12121f',
                'line': {'width': 3.0, 'color': '#A78BFA'}},
        hoverinfo='none',
        showlegend=False
    )


def build_graph_figure(input_movie: Movie,
                       recommendations: list[tuple[Movie, float]],
                       graph: WeightedGraph,
                       movies: dict[int, Movie]) -> go.Figure:
    """Builds and returns the interactive network graph.

    Shows up to 100 similar movies around the input movie at the centre.
    Distance from the centre and line thickness reflects similarity: closer and thicker means more similar.
    Top 5 recommendations have labels always visible.
    All other movies have labels when cursor is on them. At the start it is zoomed on the input
    movie by default. The user can zoom and pan to see other nodes (dragmode='pan')

    Preconditions:
        - len(recommendations) <= 5
        - input_movie.movie_id in movies
    """
    top5_ids = {mov.movie_id for mov, _ in recommendations}
    hundred_movies = _get_hundred_movies(input_movie.movie_id, graph, movies)
    positions = _compute_positions(hundred_movies)

    edge_traces = _build_edge_traces(hundred_movies, top5_ids, positions)
    other_trace = _build_other_trace(hundred_movies, top5_ids, positions)
    top5_trace = _build_top5_trace(hundred_movies, top5_ids, positions)
    input_trace = _build_input_trace(input_movie)

    fig = go.Figure(data=edge_traces + [other_trace, top5_trace, input_trace])
    fig.update_layout(
        paper_bgcolor='#0a0a12',
        plot_bgcolor='#0a0a12',
        showlegend=False,
        xaxis={'showgrid': False, 'zeroline': False, 'showticklabels': False,
               'range': [-2.0, 2.0]},
        yaxis={'showgrid': False, 'zeroline': False, 'showticklabels': False,
               'range': [-2.0, 2.0]},
        margin={'l': 20, 'r': 20, 't': 20, 'b': 20},
        dragmode='pan'
    )
    fig.update_layout(
        modebar={'remove': ['select2d', 'lasso2d', 'toImage', 'resetScale2d',
                            'hoverClosestCartesian', 'hoverCompareCartesian',
                            'toggleSpikelines', 'autoScale2d']}
    )

    return fig


if __name__ == '__main__':
    import python_ta

    python_ta.check_all(config={
        'extra-imports': ['math', 'plotly.graph_objects', 'data_loader', 'graph'],
        'max-line-length': 120,
    })
