"""Project 2: MovieMatch: interface.py

This module builds the MovieMatch desktop application using Tkinter.

Users type a movie title into the search bar (with live autocomplete),
choose a minimum average rating, and press Enter or click "Find movies"
to get up to 5 recommendations. Each recommendation is shown as a card that looks
like a VHS tape, with:
    - its title and year
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

# Colours: an old video rental store (also used in visualisations.py)
BLUE = '#1d3bb3'        # store wall blue, the window background
INK = '#0e1a4d'         # dark navy for text and outlines on white
GOLD = '#ffc93c'        # marigold for the title, buttons and selected options
WHITE = '#ffffff'
PALE = '#dfe6ff'        # light text on the blue background
GREY = '#4a557f'        # secondary text on white cards
HOVER = '#fff6d8'       # card colour when the mouse is over it
WARN = '#ffb4a8'

# Each result card gets a coloured stripe down its left side, like the spine of a VHS tape
SPINE_COLOURS = ['#e63946', '#2a9d8f', '#f4a261', '#8e5cd9', '#3aa0d8']

TITLE_FONT = 'Futura'       # bold, rounded letters for the title and movie names
FONT = 'Avenir Next'        # everything else
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
    """Return a clickable label styled as a button with a thick outline.

    A Label is used instead of tk.Button because macOS ignores button colours.
    Primary buttons are gold; the others are outlined in gold.
    """
    if primary:
        normal, hover, text_colour, outline = GOLD, WHITE, INK, INK
    else:
        normal, hover, text_colour, outline = BLUE, INK, GOLD, GOLD
    button = tk.Label(parent, text=text, bg=normal, fg=text_colour, font=(TITLE_FONT, 14, 'bold'),
                      cursor='hand2', padx=18, pady=8,
                      highlightthickness=3, highlightbackground=outline, highlightcolor=outline)
    button.bind('<Button-1>', lambda _e: command())
    button.bind('<Enter>', lambda _e: button.configure(bg=hover))
    button.bind('<Leave>', lambda _e: button.configure(bg=normal))
    return button


def _section_label(parent: tk.Widget, text: str) -> tk.Label:
    """Return a small heading for a part of the window."""
    return tk.Label(parent, text=text, bg=BLUE, fg=PALE, font=(FONT, 13, 'bold'))


# Window sections

def _setup_window() -> tk.Tk:
    """Return the main window."""
    window = tk.Tk()
    window.title('MovieMatch')
    window.configure(bg=BLUE)
    height = min(820, window.winfo_screenheight() - 80)  # fit smaller laptop screens
    window.geometry(f'1000x{height}')
    window.minsize(820, 640)
    return window


def _setup_header(window: tk.Tk) -> None:
    """Build the big title and the one-line description under it."""
    header = tk.Frame(window, bg=BLUE)
    header.pack(fill='x', padx=32, pady=(12, 0))
    tk.Label(header, text='MovieMatch', bg=BLUE, fg=GOLD,
             font=(TITLE_FONT, 46, 'bold')).pack(anchor='w')
    tk.Label(header, text='Tell it a movie you love. It finds five more.',
             bg=BLUE, fg=PALE, font=(FONT, 16)).pack(anchor='w')


def _setup_search(parent: tk.Frame, titles: list[str], on_submit: Callable[[], None],
                  heading: str, start_focused: bool = False) -> tk.StringVar:
    """Build a search bar with an autocomplete dropdown inside parent.

    As the user types, up to MAX_SUGGESTIONS matching titles appear below the bar.
    Clicking a suggestion (or pressing Down then Enter) fills the search bar.
    Pressing Enter in the search bar calls on_submit.

    Returns the search variable (to read what was typed).
    """
    section = tk.Frame(parent, bg=BLUE)
    section.pack(side='left', fill='x', expand=True, anchor='n', padx=(0, 12))
    _section_label(section, heading).pack(anchor='w', pady=(0, 6))

    search_var = tk.StringVar()
    entry_border = tk.Frame(section, bg=INK)
    entry_border.pack(fill='x')
    entry = tk.Entry(entry_border, textvariable=search_var, bg=WHITE, fg=INK,
                     font=(FONT, 16), insertbackground=INK, relief='flat',
                     highlightthickness=0)
    entry.pack(fill='x', padx=3, pady=3, ipady=8, ipadx=10)
    if start_focused:
        entry.focus_set()

    dropdown = tk.Listbox(section, bg=WHITE, fg=INK, selectbackground=GOLD,
                          selectforeground=INK, font=(FONT, 13), height=MAX_SUGGESTIONS,
                          relief='flat', highlightthickness=3, highlightbackground=INK,
                          activestyle='none')

    def on_focus(focused: bool) -> None:
        """Highlight the search bar border while it has focus."""
        entry_border.configure(bg=GOLD if focused else INK)

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


def _setup_rating_filter(controls: tk.Frame, on_change: Callable[[], None]) -> tk.DoubleVar:
    """Build the minimum rating selector as a row of clickable star options.

    Clicking an option calls on_change, so the results update straight away.
    Returns the variable holding the chosen minimum rating (0.0 means "any").
    """
    rating_var = tk.DoubleVar(value=0.0)
    box = tk.Frame(controls, bg=BLUE)
    box.pack(side='left')

    pills: dict[float, tk.Label] = {}

    def select(value: float) -> None:
        """Mark the chosen rating option as active and update the results."""
        rating_var.set(value)
        for option, pill in pills.items():
            active = option == value
            pill.configure(bg=GOLD if active else BLUE, fg=INK if active else GOLD)
        on_change()

    # only 3 movies average 4.5 or more, so the options stop at 4.0
    for value in (0.0, 3.5, 4.0):
        text = 'Any rating' if value == 0.0 else f'★ {value}+'
        pill = tk.Label(box, text=text, bg=BLUE, fg=GOLD, font=(FONT, 13, 'bold'),
                        padx=12, pady=5, cursor='hand2', highlightthickness=2,
                        highlightbackground=GOLD, highlightcolor=GOLD)
        pill.pack(side='left', padx=(0, 8))
        pill.bind('<Button-1>', lambda _e, v=value: select(v))
        pills[value] = pill

    rating_var.set(0.0)
    pills[0.0].configure(bg=GOLD, fg=INK)
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


def _build_result_card(parent: tk.Frame, rank: int, movie: Movie, searched: Movie,
                       percent: float) -> None:
    """Add one result card to parent, drawn like a VHS tape with a coloured spine.

    percent is how rare this match is, from top_percent.
    """
    card = tk.Frame(parent, bg=WHITE, highlightthickness=3, highlightbackground=INK)
    card.pack(fill='x', pady=4)

    spine_colour = SPINE_COLOURS[(rank - 1) % len(SPINE_COLOURS)]
    tk.Frame(card, bg=spine_colour, width=18).pack(side='left', fill='y')

    middle = tk.Frame(card, bg=WHITE)
    middle.pack(side='left', fill='x', expand=True, padx=14, pady=8)
    name, year = _split_title(movie.title)
    title_row = tk.Frame(middle, bg=WHITE)
    title_row.pack(anchor='w')
    tk.Label(title_row, text=name, bg=WHITE, fg=INK, font=(TITLE_FONT, 18, 'bold')).pack(side='left')
    if year:
        tk.Label(title_row, text=f'  {year}', bg=WHITE, fg=GREY, font=(FONT, 14)).pack(side='left')
    tk.Label(middle, text=_shared_features(searched, movie), bg=WHITE, fg=GREY,
             font=(FONT, 13)).pack(anchor='w', pady=(2, 0))

    right = tk.Frame(card, bg=WHITE)
    right.pack(side='right', padx=16, pady=8)
    tk.Label(right, text=_match_text(percent), bg=WHITE, fg=INK,
             font=(TITLE_FONT, 17, 'bold')).pack(anchor='e')
    info_row = tk.Frame(right, bg=WHITE)
    info_row.pack(anchor='e')
    tk.Label(info_row, text=f'★ {movie.avg_rating:.1f}', bg=WHITE, fg=GREY,
             font=(FONT, 13)).pack(side='left')
    if movie.imdb_id:
        link = tk.Label(info_row, text='   IMDb', bg=WHITE, fg=BLUE,
                        font=(FONT, 13, 'underline'), cursor='hand2')
        link.pack(side='left')
        url = f'https://www.imdb.com/title/tt{movie.imdb_id}/'
        link.bind('<Button-1>', lambda _e: webbrowser.open(url))

    # every part of the card except the spine, so they can change colour together
    card_parts = [card, middle, title_row, right, info_row]
    card_parts = card_parts + list(middle.winfo_children()) + list(title_row.winfo_children())
    card_parts = card_parts + list(right.winfo_children()) + list(info_row.winfo_children())

    def set_bg(colour: str) -> None:
        """Change the background colour of the whole card."""
        for part in card_parts:
            part.configure(bg=colour)

    def on_leave(_event: tk.Event) -> None:
        """Remove the hover colour only when the pointer has really left the card."""
        under = card.winfo_containing(card.winfo_pointerx(), card.winfo_pointery())
        if under is None or not str(under).startswith(str(card)):
            set_bg(WHITE)

    card.bind('<Enter>', lambda _e: set_bg(HOVER))
    card.bind('<Leave>', on_leave)


def run_app(movies: dict[int, Movie], graph: WeightedGraph) -> None:
    """Create the MovieMatch window and start the Tkinter event loop."""
    window = _setup_window()
    title_map = title_to_id(movies)
    titles = sorted(title_map.keys())
    lowered_to_title = {t.lower(): t for t in titles}
    graph_path = os.path.join(tempfile.gettempdir(), 'moviematch_graph.html')

    _setup_header(window)

    # used to turn similarity scores into "Top x%" ranks
    all_scores = graph.all_scores()
    total_pairs = len(movies) * (len(movies) - 1) // 2

    def add_card(rank: int, movie: Movie, score: float, compared_to: Movie) -> None:
        """Add a result card, working out how rare and how strong the match is."""
        percent = top_percent(score, all_scores, total_pairs)
        _build_result_card(results, rank, movie, compared_to, percent)

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
            status.configure(text=f'Because you liked {_split_title(title)[0]}', fg=WHITE)
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
        status.configure(text=f'Watch together: {_split_title(path[middle].title)[0]}', fg=WHITE)

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

    search_row = tk.Frame(window, bg=BLUE)
    search_row.pack(fill='x', padx=(32, 20), pady=(12, 0))
    search_var = _setup_search(search_row, titles, on_search, 'A movie you like', start_focused=True)
    friend_var = _setup_search(search_row, titles, on_search, "Your friend's favourite (optional)")

    controls = tk.Frame(window, bg=BLUE)
    controls.pack(fill='x', padx=32, pady=(12, 0))
    def on_rating_change() -> None:
        """Search again with the new minimum rating, if something has been typed."""
        if search_var.get().strip():
            on_search()

    rating_var = _setup_rating_filter(controls, on_rating_change)
    _make_button(controls, 'Find movies', on_search).pack(side='right', padx=(10, 0))
    graph_button = _make_button(controls, 'See the map', open_graph, primary=False)

    status = tk.Label(window, text='Start with a movie, like Toy Story.',
                      bg=BLUE, fg=PALE, font=(TITLE_FONT, 22, 'bold'), anchor='w')
    status.pack(fill='x', padx=32, pady=(10, 2))

    results = tk.Frame(window, bg=BLUE)
    results.pack(fill='both', expand=True, padx=32)

    tk.Label(window, text='Made by Capucine, Mavi, Syaikha and Tamima. Ratings from MovieLens.',
             bg=BLUE, fg=PALE, font=(FONT, 11)).pack(side='bottom', pady=8)

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
