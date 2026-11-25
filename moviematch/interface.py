"""Project 2: MovieMatch: interface.py

This module builds the MovieMatch desktop application using Tkinter.

Users type a movie title into the search bar (with live autocomplete),
choose a minimum average rating, and press Enter or click "Find something to watch"
to get up to 5 recommendations. Each recommendation is shown as a ticket-style card with:
    - its rank, title, and genres
    - how rare the match is (for example "Top 0.4%" of all movie pairs)
    - its average rating
    - a short "why" line listing the genres and tags both movies share
    - a link that opens the movie's IMDb page in the web browser

A button also opens an interactive Plotly network graph in the web browser
showing how the searched movie connects to up to 100 similar movies.

Copyright (c) 2026 <Capucine, Mavi, Syaikha, Tamima>
"""

from __future__ import annotations

import os
import tempfile
import tkinter as tk
import webbrowser
from collections.abc import Callable

from moviematch.data_loader import Movie
from moviematch.graph import WeightedGraph
from moviematch.recommender import find_bridge, recommend_with_min_rating, title_to_id, top_percent
from moviematch.visualisations import build_graph_figure

# Colours: a dark "movie theatre" palette (also used in visualisations.py)
BG = '#15110e'          # background, like a dark cinema
CARD = '#211a15'        # result cards
CARD_HOVER = '#2b221b'
FIELD = '#2a211a'       # search boxes
BORDER = '#3d3128'
RED = '#b3322b'         # cinema seat red, used for buttons and ticket stubs
RED_LIGHT = '#cf4038'
AMBER = '#e9a23b'       # marquee light amber, used for highlights
TEXT = '#f3e9d7'        # warm cream instead of plain white
MUTED = '#a39280'
WARN = '#e2725b'

FONT = 'Helvetica'      # normal text
TITLE_FONT = 'Georgia'  # headings, gives a classic movie poster feel
MONO_FONT = 'Courier'   # ticket numbers and small labels
MAX_SUGGESTIONS = 8


# Small helpers

def _split_title(title: str) -> tuple[str, str]:
    """Split a title like 'Toy Story (1995)' into ('Toy Story', '1995').

    If the title does not end with a 4-digit year in parentheses, the year is ''.

    >>> _split_title('Toy Story (1995)')
    ('Toy Story', '1995')
    >>> _split_title('Untitled')
    ('Untitled', '')
    """
    if len(title) >= 7 and title[-1] == ')' and title[-6] == '(' and title[-5:-1].isdigit():
        return title[:-7], title[-5:-1]
    return title, ''


def _shared_features(movie1: Movie, movie2: Movie, max_tags: int = 3) -> str:
    """Return a short sentence describing what two movies have in common.

    This explains a recommendation to the user by listing shared genres and
    up to max_tags shared user tags.

    >>> m1 = Movie(1, 'A (2000)')
    >>> m2 = Movie(2, 'B (2001)')
    >>> m1.genres, m2.genres = {'Comedy', 'Drama'}, {'Comedy'}
    >>> m1.tags, m2.tags = {'pixar'}, {'pixar', 'funny'}
    >>> _shared_features(m1, m2)
    'Shared: Comedy  ·  #pixar'
    """
    genres = sorted(movie1.genres & movie2.genres)
    tags = sorted(movie1.tags & movie2.tags)[:max_tags]
    parts = genres + ['#' + tag for tag in tags]
    if not parts:
        return 'Loved by the same audience'
    return 'Shared: ' + '  ·  '.join(parts)


def _make_button(parent: tk.Widget, text: str, command: Callable[[], None],
                 primary: bool = True) -> tk.Label:
    """Return a flat, clickable label styled as a button.

    A Label is used instead of tk.Button because macOS ignores button colours.
    """
    normal = RED if primary else FIELD
    hover = RED_LIGHT if primary else CARD_HOVER
    button = tk.Label(parent, text=text, bg=normal, fg=TEXT,
                      font=(FONT, 12, 'bold'), cursor='hand2', padx=18, pady=9)
    button.bind('<Button-1>', lambda _e: command())
    button.bind('<Enter>', lambda _e: button.configure(bg=hover))
    button.bind('<Leave>', lambda _e: button.configure(bg=normal))
    return button


def _section_label(parent: tk.Widget, text: str) -> tk.Label:
    """Return a small uppercase section heading."""
    return tk.Label(parent, text=text, bg=BG, fg=AMBER, font=(MONO_FONT, 12, 'bold'))


# Window sections

def _setup_window() -> tk.Tk:
    """Return the main window."""
    window = tk.Tk()
    window.title('MovieMatch')
    window.configure(bg=BG)
    height = min(820, window.winfo_screenheight() - 80)  # fit smaller laptop screens
    window.geometry(f'1000x{height}')
    window.minsize(820, 640)
    return window


def _setup_header(window: tk.Tk, movie_count: int, edge_count: int) -> None:
    """Build the title, tagline, and a line of dataset numbers at the top of the window."""
    header = tk.Frame(window, bg=BG)
    header.pack(fill='x', padx=32, pady=(14, 0))

    top_row = tk.Frame(header, bg=BG)
    top_row.pack(fill='x')
    tk.Label(top_row, text='MovieMatch', bg=BG, fg=TEXT,
             font=(TITLE_FONT, 34, 'bold italic')).pack(side='left')
    numbers = f'{movie_count:,} FILMS  ·  {edge_count:,} CONNECTIONS  ·  100,836 RATINGS'
    tk.Label(top_row, text=numbers, bg=BG, fg=MUTED,
             font=(MONO_FONT, 11)).pack(side='right', anchor='s', pady=(0, 8))

    tk.Label(header, text="Tell us a film you love, and we'll find what to watch next.",
             bg=BG, fg=MUTED, font=(TITLE_FONT, 14, 'italic')).pack(anchor='w')

    # a thin amber line under the header, like a marquee
    tk.Frame(header, bg=AMBER, height=2).pack(fill='x', pady=(10, 0))


def _setup_search(parent: tk.Frame, titles: list[str], on_submit: Callable[[], None],
                  heading: str, start_focused: bool = False) -> tk.StringVar:
    """Build a search bar with an autocomplete dropdown inside parent.

    As the user types, up to MAX_SUGGESTIONS matching titles appear below the bar.
    Clicking a suggestion (or pressing Down then Enter) fills the search bar.
    Pressing Enter in the search bar calls on_submit.

    Returns the search variable (to read what was typed).
    """
    section = tk.Frame(parent, bg=BG)
    section.pack(side='left', fill='x', expand=True, anchor='n', padx=(0, 12))
    _section_label(section, heading).pack(anchor='w', pady=(0, 6))

    search_var = tk.StringVar()
    entry_border = tk.Frame(section, bg=BORDER)
    entry_border.pack(fill='x')
    entry = tk.Entry(entry_border, textvariable=search_var, bg=FIELD, fg=TEXT,
                     font=(FONT, 15), insertbackground=TEXT, relief='flat',
                     highlightthickness=0)
    entry.pack(fill='x', padx=1, pady=1, ipady=10, ipadx=10)
    if start_focused:
        entry.focus_set()

    dropdown = tk.Listbox(section, bg=CARD, fg=TEXT, selectbackground=RED,
                          selectforeground=TEXT, font=(FONT, 13), height=MAX_SUGGESTIONS,
                          relief='flat', highlightthickness=1, highlightbackground=BORDER,
                          activestyle='none')

    def on_focus(focused: bool) -> None:
        """Highlight the search bar border while it has focus."""
        entry_border.configure(bg=AMBER if focused else BORDER)

    def hide_dropdown() -> None:
        """Hide the suggestion list."""
        dropdown.pack_forget()

    def on_type(*_: object) -> None:
        """Update the suggestion list as the user types."""
        typed = search_var.get().strip().lower()
        dropdown.delete(0, tk.END)
        if not typed or typed in lowered_titles:
            hide_dropdown()
            return

        # Titles that start with the typed text come first, then titles that contain it.
        starts = [t for t in titles if t.lower().startswith(typed)]
        contains = [t for t in titles if typed in t.lower() and not t.lower().startswith(typed)]
        matches = (starts + contains)[:MAX_SUGGESTIONS]

        if not matches:
            hide_dropdown()
            return

        for match in matches:
            dropdown.insert(tk.END, '  ' + match)
        dropdown.configure(height=len(matches))
        dropdown.pack(fill='x')

    def choose(index: int) -> None:
        """Fill the search bar with the suggestion at index."""
        search_var.set(dropdown.get(index).strip())
        hide_dropdown()
        entry.icursor(tk.END)
        entry.focus_set()

    def on_select(_event: tk.Event) -> None:
        """Fill the search bar when the user clicks a suggestion."""
        if dropdown.curselection():
            choose(dropdown.curselection()[0])

    def on_down(_event: tk.Event) -> str:
        """Move keyboard focus from the search bar into the suggestion list."""
        if dropdown.winfo_ismapped() and dropdown.size() > 0:
            dropdown.focus_set()
            dropdown.selection_clear(0, tk.END)
            dropdown.selection_set(0)
            dropdown.activate(0)
        return 'break'

    def on_dropdown_enter(_event: tk.Event) -> None:
        """Choose the highlighted suggestion with the Enter key."""
        if dropdown.curselection():
            choose(dropdown.curselection()[0])

    def on_enter(_event: tk.Event) -> None:
        """Search when Enter is pressed, using the top suggestion if nothing exact was typed."""
        if dropdown.winfo_ismapped() and dropdown.size() > 0 \
                and search_var.get().strip().lower() not in lowered_titles:
            choose(0)
        hide_dropdown()
        on_submit()

    lowered_titles = {t.lower() for t in titles}
    search_var.trace_add('write', on_type)
    entry.bind('<FocusIn>', lambda _e: on_focus(True))
    entry.bind('<FocusOut>', lambda _e: on_focus(False))
    entry.bind('<Return>', on_enter)
    entry.bind('<Down>', on_down)
    entry.bind('<Escape>', lambda _e: hide_dropdown())
    dropdown.bind('<ButtonRelease-1>', on_select)
    dropdown.bind('<Return>', on_dropdown_enter)
    dropdown.bind('<Escape>', lambda _e: (hide_dropdown(), entry.focus_set()))

    return search_var


def _setup_rating_filter(controls: tk.Frame) -> tk.DoubleVar:
    """Build the minimum rating selector as a row of clickable star options.

    Returns the variable holding the chosen minimum rating (0.0 means "any").
    """
    rating_var = tk.DoubleVar(value=0.0)
    box = tk.Frame(controls, bg=BG)
    box.pack(side='left')
    tk.Label(box, text='RATED AT LEAST', bg=BG, fg=AMBER,
             font=(MONO_FONT, 12, 'bold')).pack(side='left', padx=(0, 10))

    pills: dict[float, tk.Label] = {}

    def select(value: float) -> None:
        """Mark the chosen rating option as active."""
        rating_var.set(value)
        for option, pill in pills.items():
            active = option == value
            pill.configure(bg=RED if active else FIELD, fg=TEXT if active else MUTED)

    for value in (0.0, 3.0, 3.5, 4.0, 4.5):
        text = 'Any' if value == 0.0 else f'★ {value}+'
        pill = tk.Label(box, text=text, bg=FIELD, fg=MUTED, font=(FONT, 11, 'bold'),
                        padx=10, pady=6, cursor='hand2')
        pill.pack(side='left', padx=2)
        pill.bind('<Button-1>', lambda _e, v=value: select(v))
        pills[value] = pill

    select(0.0)
    return rating_var


def _match_text(percent: float) -> str:
    """Return a short label like 'Top 0.4%' for a top_percent value.

    >>> _match_text(0.024)
    'Top 0.02%'
    >>> _match_text(2.28)
    'Top 2.3%'
    >>> _match_text(0.001)
    'Top 0.01%'
    """
    if percent < 0.01:
        percent = 0.01
    if percent < 1:
        return f'Top {percent:.2f}%'
    return f'Top {percent:.1f}%'


def _draw_match_bar(parent: tk.Widget, strength: float, width: int = 120) -> tk.Canvas:
    """Return a small bar filled in proportion to strength (between 0.0 and 1.0)."""
    canvas = tk.Canvas(parent, width=width, height=6, bg=CARD, highlightthickness=0)
    canvas.create_rectangle(0, 0, width, 6, fill=FIELD, outline='')
    filled = max(4, int(width * min(strength, 1.0)))
    canvas.create_rectangle(0, 0, filled, 6, fill=AMBER, outline='')
    return canvas


def _build_result_card(parent: tk.Frame, rank: int, movie: Movie, searched: Movie,
                       percent: float, strength: float) -> None:
    """Add one result card to parent, styled like a cinema ticket.

    percent is how rare this match is (from top_percent) and strength is how strong
    it is compared to all other connections in the graph (0.0 to 1.0).
    """
    card = tk.Frame(parent, bg=CARD)
    card.pack(fill='x', pady=3)

    # the red "ticket stub" on the left with the number
    stub = tk.Frame(card, bg=RED, width=70)
    stub.pack(side='left', fill='y')
    stub.pack_propagate(False)
    tk.Label(stub, text='No.', bg=RED, fg=TEXT, font=(MONO_FONT, 10)).pack(pady=(8, 0))
    tk.Label(stub, text=f'{rank:02d}', bg=RED, fg=TEXT, font=(MONO_FONT, 22, 'bold')).pack()

    # dashed line between the stub and the ticket, like perforations
    perforation = tk.Canvas(card, width=10, height=80, bg=CARD, highlightthickness=0)
    perforation.create_line(5, 0, 5, 80, fill=BORDER, dash=(3, 3), width=2)
    perforation.pack(side='left', fill='y')

    middle = tk.Frame(card, bg=CARD)
    middle.pack(side='left', fill='x', expand=True, pady=7, padx=(8, 0))
    name, year = _split_title(movie.title)
    title_row = tk.Frame(middle, bg=CARD)
    title_row.pack(anchor='w')
    tk.Label(title_row, text=name, bg=CARD, fg=TEXT, font=(TITLE_FONT, 16, 'bold')).pack(side='left')
    if year:
        tk.Label(title_row, text=f'  ({year})', bg=CARD, fg=MUTED, font=(TITLE_FONT, 13)).pack(side='left')
    genres = '  ·  '.join(sorted(movie.genres)) or 'Unknown genre'
    tk.Label(middle, text=genres, bg=CARD, fg=MUTED, font=(FONT, 11)).pack(anchor='w', pady=(2, 0))
    tk.Label(middle, text=_shared_features(searched, movie), bg=CARD, fg=AMBER,
             font=(TITLE_FONT, 12, 'italic')).pack(anchor='w', pady=(4, 0))

    right = tk.Frame(card, bg=CARD)
    right.pack(side='right', padx=18, pady=7)
    match_row = tk.Frame(right, bg=CARD)
    match_row.pack(anchor='e')
    tk.Label(match_row, text=_match_text(percent), bg=CARD, fg=AMBER,
             font=(MONO_FONT, 15, 'bold')).pack(side='left')
    tk.Label(match_row, text=' of all pairs', bg=CARD, fg=MUTED,
             font=(FONT, 10)).pack(side='left')
    _draw_match_bar(right, strength).pack(anchor='e', pady=(4, 4))
    rating_row = tk.Frame(right, bg=CARD)
    rating_row.pack(anchor='e')
    tk.Label(rating_row, text=f'★ {movie.avg_rating:.1f}', bg=CARD, fg=TEXT,
             font=(FONT, 12, 'bold')).pack(side='left')
    if movie.imdb_id:
        link = tk.Label(rating_row, text='   IMDb ↗', bg=CARD, fg=MUTED,
                        font=(FONT, 11, 'underline'), cursor='hand2')
        link.pack(side='left')
        url = f'https://www.imdb.com/title/tt{movie.imdb_id}/'
        link.bind('<Button-1>', lambda _e: webbrowser.open(url))
        link.bind('<Enter>', lambda _e: link.configure(fg=TEXT))
        link.bind('<Leave>', lambda _e: link.configure(fg=MUTED))

    def set_bg(colour: str) -> None:
        """Recolour the ticket (but not the red stub) when the mouse is over it."""
        widgets = [card, perforation, middle, right, title_row, rating_row, match_row]
        widgets = widgets + list(middle.winfo_children()) + list(right.winfo_children())
        widgets = widgets + list(title_row.winfo_children()) + list(rating_row.winfo_children())
        widgets = widgets + list(match_row.winfo_children())
        for widget in widgets:
            widget.configure(bg=colour)

    def on_leave(_event: tk.Event) -> None:
        """Remove the hover colour only when the pointer has really left the card."""
        under = card.winfo_containing(card.winfo_pointerx(), card.winfo_pointery())
        if under is None or not str(under).startswith(str(card)):
            set_bg(CARD)

    card.bind('<Enter>', lambda _e: set_bg(CARD_HOVER))
    card.bind('<Leave>', on_leave)


def _count_edges(graph: WeightedGraph, movies: dict[int, Movie]) -> int:
    """Return the number of edges in graph (each edge is counted once)."""
    return sum(len(graph.get_neighbours(movie_id)) for movie_id in movies) // 2


def run_app(movies: dict[int, Movie], graph: WeightedGraph) -> None:
    """Create the MovieMatch window and start the Tkinter event loop."""
    window = _setup_window()
    title_map = title_to_id(movies)
    titles = sorted(title_map.keys())
    lowered_to_title = {t.lower(): t for t in titles}
    graph_path = os.path.join(tempfile.gettempdir(), 'moviematch_graph.html')

    _setup_header(window, len(movies), _count_edges(graph, movies))

    # used to turn similarity scores into "Top x%" ranks
    all_scores = graph.all_scores()
    total_pairs = len(movies) * (len(movies) - 1) // 2

    def add_card(rank: int, movie: Movie, score: float, compared_to: Movie) -> None:
        """Add a result card, working out how rare and how strong the match is."""
        percent = top_percent(score, all_scores, total_pairs)
        strength = 1 - top_percent(score, all_scores, len(all_scores)) / 100
        _build_result_card(results, rank, movie, compared_to, percent, strength)

    state: dict[str, bool] = {'graph_ready': False}

    def on_search() -> None:
        """Find recommendations for the typed movie and show them as cards."""
        typed = search_var.get().strip()
        title = lowered_to_title.get(typed.lower())

        for child in results.winfo_children():
            child.destroy()

        if title is None:
            status.configure(text='Movie not found. Pick a title from the suggestions as you type.', fg=WARN)
            graph_button.pack_forget()
            return

        search_var.set(title)

        # if a friend's movie was also typed, switch to bridge mode
        friend_typed = friend_var.get().strip()
        if friend_typed:
            friend_title = lowered_to_title.get(friend_typed.lower())
            if friend_title is None:
                status.configure(text="Your friend's movie was not found. Pick it from the suggestions.", fg=WARN)
                graph_button.pack_forget()
                return
            friend_var.set(friend_title)
            on_bridge(title, friend_title)
            return

        searched = movies[title_map[title]]
        min_rating = rating_var.get()
        recommendations = recommend_with_min_rating(title, graph, movies, min_rating)

        if recommendations:
            status.configure(text=f'Because you liked {title}', fg=TEXT)
        elif min_rating > 0:
            status.configure(text=f'No similar movies rated ★ {min_rating}+. Try a lower minimum rating.', fg=WARN)
        else:
            status.configure(text='This movie has no close matches in the graph yet.', fg=WARN)

        for rank, (movie, score) in enumerate(recommendations, start=1):
            add_card(rank, movie, score, searched)

        fig = build_graph_figure(searched, recommendations, graph, movies)
        fig.write_html(graph_path)
        state['graph_ready'] = True
        graph_button.pack(side='right')

    def on_bridge(title1: str, title2: str) -> None:
        """Show the chain of movies that connects two people's favourite movies."""
        graph_button.pack_forget()
        path = find_bridge(title1, title2, graph, movies)

        if len(path) < 3:
            status.configure(text="Couldn't find a movie between these two. Try two different movies.", fg=WARN)
            return

        middle = len(path) // 2
        status.configure(text=f'Watch together: {path[middle].title}', fg=TEXT)

        # one card per step, explaining how each movie links to the one before it
        for step in range(1, len(path)):
            previous = path[step - 1]
            movie = path[step]
            score = 0.0
            for neighbour, neighbour_score in graph.get_neighbours(previous.movie_id):
                if neighbour.movie_id == movie.movie_id:
                    score = neighbour_score
            add_card(step, movie, score, previous)

    def open_graph() -> None:
        """Open the network graph for the latest search in the web browser."""
        if state['graph_ready']:
            webbrowser.open('file://' + graph_path)

    search_row = tk.Frame(window, bg=BG)
    search_row.pack(fill='x', padx=(32, 20), pady=(16, 0))
    search_var = _setup_search(search_row, titles, on_search, 'I LIKE...', start_focused=True)
    friend_var = _setup_search(search_row, titles, on_search, "MY FRIEND LIKES... (OPTIONAL)")

    controls = tk.Frame(window, bg=BG)
    controls.pack(fill='x', padx=32, pady=(12, 0))
    rating_var = _setup_rating_filter(controls)
    _make_button(controls, 'Find something to watch', on_search).pack(side='right', padx=(10, 0))
    graph_button = _make_button(controls, 'View graph ↗', open_graph, primary=False)

    status = tk.Label(window, text='Try "Toy Story", or add a friend\'s favourite to find a movie you both like.',
                      bg=BG, fg=MUTED, font=(TITLE_FONT, 16, 'italic'), anchor='w')
    status.pack(fill='x', padx=32, pady=(16, 4))

    results = tk.Frame(window, bg=BG)
    results.pack(fill='both', expand=True, padx=32)

    tk.Label(window, text='made by Capucine, Mavi, Syaikha & Tamima  ·  ratings from MovieLens',
             bg=BG, fg=MUTED, font=(TITLE_FONT, 11, 'italic')).pack(side='bottom', pady=8)

    window.mainloop()


if __name__ == '__main__':
    import doctest
    doctest.testmod()

    import python_ta

    python_ta.check_all(config={
        'extra-imports': [
            'os', 'tempfile', 'webbrowser', 'tkinter',
            'moviematch.data_loader', 'moviematch.graph', 'moviematch.recommender', 'moviematch.visualisations'
        ],
        'allowed-io': ['on_search'],
        'max-line-length': 120,
    })
