"""Project 2: MovieMatch: interface.py

This module builds the MovieMatch desktop application using Tkinter.

Users type a movie title into the search bar (with live autocomplete),
choose a minimum average rating, and press Enter or click "Find matches"
to get up to 5 recommendations. Each recommendation is shown as a card with:
    - its rank, title, and genres
    - its average rating and number of ratings
    - a bar showing how similar it is to the searched movie
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
from moviematch.posters import get_poster
from moviematch.recommender import find_bridge, recommend_with_min_rating, title_to_id
from moviematch.visualisations import build_graph_figure

# Colour palette (shared with the Plotly graph in visualisations.py)
BG = '#0a0a12'
CARD = '#12121f'
CARD_HOVER = '#191930'
FIELD = '#181828'
BORDER = '#25254a'
PURPLE = '#A78BFA'
PURPLE_DARK = '#4F46E5'
BLUE = '#60A5FA'
TEXT = '#ffffff'
MUTED = '#8b8ba7'
GOLD = '#FBBF24'
WARN = '#F87171'

FONT = 'Helvetica'
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
    normal = PURPLE_DARK if primary else FIELD
    hover = PURPLE if primary else CARD_HOVER
    button = tk.Label(parent, text=text, bg=normal, fg=TEXT,
                      font=(FONT, 12, 'bold'), cursor='hand2', padx=18, pady=9)
    button.bind('<Button-1>', lambda _e: command())
    button.bind('<Enter>', lambda _e: button.configure(bg=hover))
    button.bind('<Leave>', lambda _e: button.configure(bg=normal))
    return button


def _section_label(parent: tk.Widget, text: str) -> tk.Label:
    """Return a small uppercase section heading."""
    return tk.Label(parent, text=text, bg=BG, fg=PURPLE, font=(FONT, 10, 'bold'))


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
    """Build the title, tagline, and dataset statistics at the top of the window."""
    header = tk.Frame(window, bg=BG)
    header.pack(fill='x', padx=32, pady=(18, 0))

    top_row = tk.Frame(header, bg=BG)
    top_row.pack(fill='x')
    title_row = tk.Frame(top_row, bg=BG)
    title_row.pack(side='left')
    tk.Label(title_row, text='Movie', bg=BG, fg=TEXT,
             font=(FONT, 32, 'bold')).pack(side='left')
    tk.Label(title_row, text='Match', bg=BG, fg=PURPLE,
             font=(FONT, 32, 'bold')).pack(side='left')

    tk.Label(header, text='Find your next favourite film through a graph of what people actually love.',
             bg=BG, fg=MUTED, font=(FONT, 13)).pack(anchor='w', pady=(2, 0))

    stats = tk.Frame(top_row, bg=BG)
    stats.pack(side='right')
    for value, label in ((f'{movie_count:,}', 'movies'),
                         (f'{edge_count:,}', 'connections'),
                         ('100k+', 'ratings analysed')):
        chip = tk.Frame(stats, bg=CARD, highlightthickness=1, highlightbackground=BORDER)
        chip.pack(side='left', padx=(10, 0))
        tk.Label(chip, text=value, bg=CARD, fg=BLUE, font=(FONT, 12, 'bold')).pack(side='left', padx=(12, 4), pady=6)
        tk.Label(chip, text=label, bg=CARD, fg=MUTED, font=(FONT, 11)).pack(side='left', padx=(0, 12))


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

    dropdown = tk.Listbox(section, bg=CARD, fg=TEXT, selectbackground=PURPLE_DARK,
                          selectforeground=TEXT, font=(FONT, 13), height=MAX_SUGGESTIONS,
                          relief='flat', highlightthickness=1, highlightbackground=BORDER,
                          activestyle='none')

    def on_focus(focused: bool) -> None:
        """Highlight the search bar border while it has focus."""
        entry_border.configure(bg=PURPLE if focused else BORDER)

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
    tk.Label(box, text='MIN RATING', bg=BG, fg=PURPLE,
             font=(FONT, 10, 'bold')).pack(side='left', padx=(0, 10))

    pills: dict[float, tk.Label] = {}

    def select(value: float) -> None:
        """Mark the chosen rating option as active."""
        rating_var.set(value)
        for option, pill in pills.items():
            active = option == value
            pill.configure(bg=PURPLE_DARK if active else FIELD, fg=TEXT if active else MUTED)

    for value in (0.0, 3.0, 3.5, 4.0, 4.5):
        text = 'Any' if value == 0.0 else f'★ {value}+'
        pill = tk.Label(box, text=text, bg=FIELD, fg=MUTED, font=(FONT, 11, 'bold'),
                        padx=10, pady=6, cursor='hand2')
        pill.pack(side='left', padx=2)
        pill.bind('<Button-1>', lambda _e, v=value: select(v))
        pills[value] = pill

    select(0.0)
    return rating_var


def _draw_match_bar(parent: tk.Widget, score: float, width: int = 150) -> tk.Canvas:
    """Return a small horizontal bar filled in proportion to score (between 0.0 and 1.0)."""
    canvas = tk.Canvas(parent, width=width, height=8, bg=CARD, highlightthickness=0)
    canvas.create_rectangle(0, 0, width, 8, fill=FIELD, outline='')
    filled = max(4, int(width * min(score, 1.0)))
    canvas.create_rectangle(0, 0, filled, 8, fill=BLUE, outline='')
    return canvas


def _poster_image(movie: Movie, height: int = 64) -> tk.PhotoImage | None:
    """Return the movie's poster resized to the given height, or None if there isn't one.

    Tkinter can't open JPEG files by itself, so this uses Pillow. If Pillow is
    not installed, cards are shown without posters.
    """
    poster_bytes = get_poster(movie)
    if poster_bytes is None:
        return None
    try:
        from io import BytesIO

        from PIL import Image, ImageTk
    except ImportError:
        return None

    image = Image.open(BytesIO(poster_bytes))
    width = round(image.width * height / image.height)
    return ImageTk.PhotoImage(image.resize((width, height)))


def _build_result_card(parent: tk.Frame, rank: int, movie: Movie, score: float,
                       searched: Movie) -> None:
    """Add one recommendation card to parent."""
    card = tk.Frame(parent, bg=CARD, highlightthickness=1, highlightbackground=BORDER)
    card.pack(fill='x', pady=4)

    tk.Label(card, text=f'{rank:02d}', bg=CARD, fg=PURPLE_DARK,
             font=(FONT, 24, 'bold'), width=3).pack(side='left', padx=(10, 4), pady=8)

    poster = _poster_image(movie)
    if poster is not None:
        poster_label = tk.Label(card, image=poster, bg=CARD)
        poster_label.image = poster  # keep a reference, or Tkinter deletes the image
        poster_label.pack(side='left', padx=(0, 12), pady=6)

    middle = tk.Frame(card, bg=CARD)
    middle.pack(side='left', fill='x', expand=True, pady=8)
    name, year = _split_title(movie.title)
    title_row = tk.Frame(middle, bg=CARD)
    title_row.pack(anchor='w')
    tk.Label(title_row, text=name, bg=CARD, fg=TEXT, font=(FONT, 15, 'bold')).pack(side='left')
    if year:
        tk.Label(title_row, text=f'  {year}', bg=CARD, fg=MUTED, font=(FONT, 13)).pack(side='left')
    genres = '  ·  '.join(sorted(movie.genres)) or 'Unknown genre'
    tk.Label(middle, text=genres, bg=CARD, fg=MUTED, font=(FONT, 11)).pack(anchor='w', pady=(2, 0))
    tk.Label(middle, text=_shared_features(searched, movie), bg=CARD, fg=PURPLE,
             font=(FONT, 11, 'italic')).pack(anchor='w', pady=(4, 0))

    right = tk.Frame(card, bg=CARD)
    right.pack(side='right', padx=16, pady=8)
    rating_row = tk.Frame(right, bg=CARD)
    rating_row.pack(anchor='e')
    tk.Label(rating_row, text=f'★ {movie.avg_rating:.2f}', bg=CARD, fg=GOLD,
             font=(FONT, 13, 'bold')).pack(side='left')
    tk.Label(rating_row, text=f'  ({movie.rating_count:,})', bg=CARD, fg=MUTED,
             font=(FONT, 11)).pack(side='left')
    match_row = tk.Frame(right, bg=CARD)
    match_row.pack(anchor='e', pady=(4, 2))
    _draw_match_bar(match_row, score).pack(side='left', padx=(0, 8))
    tk.Label(match_row, text=f'{round(score * 100)}% match', bg=CARD, fg=BLUE,
             font=(FONT, 11, 'bold')).pack(side='left')

    if movie.imdb_id:
        link = tk.Label(right, text='View on IMDb ↗', bg=CARD, fg=MUTED,
                        font=(FONT, 11, 'underline'), cursor='hand2')
        link.pack(anchor='e')
        url = f'https://www.imdb.com/title/tt{movie.imdb_id}/'
        link.bind('<Button-1>', lambda _e: webbrowser.open(url))
        link.bind('<Enter>', lambda _e: link.configure(fg=TEXT))
        link.bind('<Leave>', lambda _e: link.configure(fg=MUTED))

    def set_bg(colour: str) -> None:
        """Recolour the card and every widget inside it (for the hover effect)."""
        stack: list[tk.Misc] = [card]
        while stack:
            widget = stack.pop()
            widget.configure(bg=colour)
            stack.extend(widget.winfo_children())

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
            _build_result_card(results, rank, movie, score, searched)

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
            _build_result_card(results, step, movie, score, previous)

    def open_graph() -> None:
        """Open the network graph for the latest search in the web browser."""
        if state['graph_ready']:
            webbrowser.open('file://' + graph_path)

    search_row = tk.Frame(window, bg=BG)
    search_row.pack(fill='x', padx=(32, 20), pady=(16, 0))
    search_var = _setup_search(search_row, titles, on_search, 'A MOVIE YOU LIKE', start_focused=True)
    friend_var = _setup_search(search_row, titles, on_search, "A FRIEND'S FAVOURITE (OPTIONAL)")

    controls = tk.Frame(window, bg=BG)
    controls.pack(fill='x', padx=32, pady=(12, 0))
    rating_var = _setup_rating_filter(controls)
    _make_button(controls, 'Find matches', on_search).pack(side='right', padx=(10, 0))
    graph_button = _make_button(controls, 'View graph ↗', open_graph, primary=False)

    status = tk.Label(window, text='Try "Toy Story", or add a friend\'s favourite to find a movie you both like.',
                      bg=BG, fg=MUTED, font=(FONT, 14, 'bold'), anchor='w')
    status.pack(fill='x', padx=32, pady=(16, 4))

    results = tk.Frame(window, bg=BG)
    results.pack(fill='both', expand=True, padx=32)

    tk.Label(window, text='Data: MovieLens (GroupLens Research)  ·  Built by Capucine, Mavi, Syaikha & Tamima',
             bg=BG, fg=MUTED, font=(FONT, 10)).pack(side='bottom', pady=8)

    window.mainloop()


if __name__ == '__main__':
    import doctest
    doctest.testmod()

    import python_ta

    python_ta.check_all(config={
        'extra-imports': [
            'os', 'tempfile', 'webbrowser', 'tkinter',
            'moviematch.data_loader', 'moviematch.graph', 'moviematch.posters', 'moviematch.recommender',
            'moviematch.visualisations', 'io', 'PIL'
        ],
        'allowed-io': ['on_search'],
        'max-line-length': 120,
    })
