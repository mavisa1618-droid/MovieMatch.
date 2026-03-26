"""Project 2: MovieMatch: visualisations.py

This module creates an interactive network graph that appears at the bottom of the MovieMatch
interface. When a user searches for a movie, this module takes the input movie
and its top 5 recommendations and makes a visual graph where the input movie sits
at the centre and the recommendations surround it. The thickness of each edge shows how similar
two movies are, and the size of each node reflects the movie's average rating.

"""
from __future__ import annotations
import math
import plotly.graph_objects as go
from data_loader import Movie


def _build_edge_traces(recommendations: list[tuple[Movie, float]]) -> list[go.Scatter]:
    """Return the lines connecting the centre movie to each recommendation.

    Each line's thickness reflects how similar the two movies are:
    the more similar, the thicker the line.
    """
    edge_traces = []
    for i, (_, score) in enumerate(recommendations):
        angle = 2 * math.pi * i / len(recommendations)
        x = math.cos(angle)
        y = math.sin(angle)
        edge_traces.append(go.Scatter(
            x=[0, x, None],
            y=[0, y, None],
            mode='lines',
            line={'width': score * 10, 'color': '#60A5FA'},
            hoverinfo='none',
            showlegend=False
        ))
    return edge_traces


def _build_node_trace(input_movie: Movie, recommendations: list[tuple[Movie, float]]) -> go.Scatter:
    """Return all the movie circles and their labels as a single trace.

    The input movie sits at the centre, and the recommendations
    are placed evenly around it in a circle. Bigger circles
    mean higher rated movies.
    """
    node_x = [0.0]
    node_y = [0.0]
    node_text = [f'<b>{input_movie.title}</b><br>★ {input_movie.avg_rating}']
    node_size = [input_movie.avg_rating * 10 + 30]
    node_color = ['#12121f']
    node_border_color = ['#A78BFA']
    node_border_width = [3.0]

    for i, (movie, score) in enumerate(recommendations):
        angle = 2 * math.pi * i / len(recommendations)
        node_x.append(math.cos(angle))
        node_y.append(math.sin(angle))
        node_text.append(f'{movie.title}<br>★ {movie.avg_rating} · {round(score * 100)}%')
        node_size.append(movie.avg_rating * 10 + 25)
        node_color.append('#12121f')
        node_border_color.append('#4F46E5')
        node_border_width.append(2.5)

    return go.Scatter(
        x=node_x,
        y=node_y,
        mode='markers+text',
        text=node_text,
        textposition='middle center',
        textfont={'color': 'white', 'size': 10},
        marker={
            'size': node_size,
            'color': node_color,
            'line': {'width': node_border_width, 'color': node_border_color}
        },
        hoverinfo='none',
        showlegend=False
    )


def _build_legend_traces() -> list[go.Scatter]:
    """Return the three entries shown in the legend at the bottom of the graph.
    """
    legend_input = go.Scatter(
        x=[None], y=[None],
        mode='markers',
        marker={'size': 10, 'color': '#12121f', 'line': {'width': 2, 'color': '#A78BFA'}},
        name='Input movie',
        showlegend=True
    )
    legend_rec = go.Scatter(
        x=[None], y=[None],
        mode='markers',
        marker={'size': 10, 'color': '#12121f', 'line': {'width': 2, 'color': '#4F46E5'}},
        name='Recommendation',
        showlegend=True
    )
    legend_edge = go.Scatter(
        x=[None], y=[None],
        mode='lines',
        line={'width': 3, 'color': '#60A5FA'},
        name='Similarity (thicker = more similar)',
        showlegend=True
    )
    return [legend_input, legend_rec, legend_edge]


def build_graph_figure(input_movie: Movie, recommendations: list[tuple[Movie, float]]) -> go.Figure:
    """Build and return the full network graph for a movie and its recommendations.

    The input movie appears in the centre, with its 5 recommendations
    around it. Thicker lines mean the two movies are more similar, and
    bigger circles mean higher rated movies.

    Nodes are positioned in a circle using the formula (cos(2π * i / n), sin(2π * i / n))
    where i is the node index and n is the number of recommendations.
    Node size = avg_rating * 10 + 10. Edge thickness = similarity score * 10.

    Preconditions:
        - len(recommendations) <= 5
        - all(0.0 <= score <= 1.0 for _, score in recommendations)
    """
    edge_traces = _build_edge_traces(recommendations)
    node_trace = _build_node_trace(input_movie, recommendations)
    legend_traces = _build_legend_traces()

    fig = go.Figure(data=edge_traces + [node_trace] + legend_traces)
    fig.update_layout(
        paper_bgcolor='#0a0a12',
        plot_bgcolor='#0a0a12',
        showlegend=True,
        legend={
            'font': {'color': '#6b6b8a', 'size': 11},
            'bgcolor': '#0a0a12',
            'bordercolor': '#1e1e35',
            'borderwidth': 1,
            'orientation': 'h',
            'yanchor': 'bottom',
            'y': 0.01,
            'xanchor': 'left',
            'x': 0.01
        },
        xaxis={'showgrid': False, 'zeroline': False, 'showticklabels': False},
        yaxis={'showgrid': False, 'zeroline': False, 'showticklabels': False},
        margin={'l': 20, 'r': 20, 't': 20, 'b': 60},
        hoverlabel={'bgcolor': '#12121f', 'font_color': 'white', 'bordercolor': '#A78BFA'}
    )

    return fig


if __name__ == '__main__':
    import python_ta

    python_ta.check_all(config={
        'extra-imports': ['math', 'plotly.graph_objects', 'data_loader'],
        'max-line-length': 120,
    })
