"""Project 2: MovieMatch: interface.py

This module builds the MovieMatch application using Tkinter.
Users type a movie title into the search bar, adjust the minimum rating slider,
and click search to get up to 5 recommendations. Each recommendation appears
in a table showing the title, average rating, and similarity percentage.

Clicking a row opens the movie's IMDb page in the web browser.
A clickable label also lets the user open a Plotly network graph in the web browser
showing connections between the input movie and similar movies.
"""

from __future__ import annotations
import os
import webbrowser
import tkinter as tk
from tkinter import ttk
from typing import Optional
from data_loader import Movie
from graph import WeightedGraph
from recommender import recommend_with_min_rating, title_to_id
from visualisations import build_graph_figure

BG = '#0a0a12'
BG2 = '#12121f'
PURPLE = '#A78BFA'
PURPLE_DARK = '#4F46E5'
BLUE = '#60A5FA'
BORDER = '#1e1e35'
TEXT = '#ffffff'


def _setup_window() -> tk.Tk:
    """Return the main window."""
    window = tk.Tk()
    window.title('MovieMatch')
    window.configure(bg=BG)
    window.geometry('900x800')
    window.resizable(True, True)
    return window


def _setup_search(window: tk.Tk, titles: list[str]) -> tk.StringVar:
    """Build and return the search bar and autocomplete dropdown.

    As the user types, a dropdown list appears below the search bar
    showing matching movie titles. Clicking a title fills the search bar.

    Returns the search variable (to read what was typed).
    """
    frame = tk.Frame(window, bg=BG)
    frame.pack(pady=10, padx=20, fill='x')  # full window width

    tk.Label(frame, text='SEARCH FOR A MOVIE',
             bg=BG, fg=PURPLE,
             font=('Helvetica', 10)).pack(anchor='w')  # aligned to left

    search_var = tk.StringVar()  # search_var always updated
    tk.Entry(frame, textvariable=search_var,
             bg=BG2, fg=TEXT,
             font=('Helvetica', 12),
             insertbackground=TEXT,  # white cursor
             highlightthickness=1,
             highlightbackground=BLUE,
             relief='flat').pack(fill='x', ipady=6)  # internal padding, full window width

    dropdown = tk.Listbox(frame, bg=BG2, fg=TEXT,  # hidden dropdown, no input yet
                          selectbackground=PURPLE_DARK,
                          font=('Helvetica', 11),
                          height=5,  # shows only 5 suggestions
                          relief='flat',
                          highlightthickness=1,
                          highlightbackground=BORDER)

    def on_type(*_: object) -> None:  # called when user types
        """Update the dropdown list as the user types."""
        typed = search_var.get().lower()  # current text
        dropdown.delete(0, tk.END)  # deletes old suggestions
        if not typed:
            dropdown.pack_forget()  # hides dropdown
            return

        matches = [t for t in titles if typed in t.lower()][:8]

        if matches:
            for match in matches:
                dropdown.insert(tk.END, match)
        else:
            dropdown.insert(tk.END, 'No movies match')

        dropdown.pack(fill='x')  # show dropdown

    def on_select(_event: tk.Event) -> None:  # when suggestion clicked
        """Fill the search bar when the user clicks a suggestion."""
        if dropdown.curselection():
            # gets title from tuple of indices for selected suggestion and sets it in search box
            search_var.set(dropdown.get(dropdown.curselection()))
            dropdown.pack_forget()  # hides the dropdown

    search_var.trace('w', on_type)  # when search_var updated, call on_type
    dropdown.bind('<<ListboxSelect>>', on_select)  # when user clicks, call on_select

    return search_var


def _setup_slider(window: tk.Tk) -> tk.DoubleVar:
    """Return the minimum rating slider.

    The user can drag this to filter out recommendations below
    a certain average rating. Returns the slider variable so
    run_app can read the current value when search is clicked.
    """
    frame = tk.Frame(window, bg=BG)
    frame.pack(pady=10, padx=20, fill='x')

    rating_var = tk.DoubleVar(value=0.0)  # slider starts at 0.0

    tk.Label(frame, text='MINIMUM RATING',
             bg=BG, fg=PURPLE,
             font=('Helvetica', 10)).pack(anchor='w')

    tk.Scale(frame,
             variable=rating_var,  # rating_var updates when slider is used
             from_=0.0, to=5.0,  # values from 0.0 to 5.0
             resolution=0.5,  # increase by 0.5
             orient='horizontal',  # goes left to right
             bg=BG,
             fg=TEXT,
             troughcolor=BG2,
             highlightthickness=0,
             activebackground=PURPLE).pack(fill='x')  # color when slider is used

    return rating_var


def _setup_results_table(window: tk.Tk) -> ttk.Treeview:
    """Return the results table.

    The table has three visible columns: title, average rating, and
    similarity percentage. A hidden fourth column stores the IMDb ID
    so the movie's IMDb page can be opened in the web browser when a row is clicked.
    """
    frame = tk.Frame(window, bg=BG)
    frame.pack(pady=10, padx=20, fill='x')

    tk.Label(frame, text='RECOMMENDATIONS',
             bg=BG, fg=PURPLE,
             font=('Helvetica', 10)).pack(anchor='w')

    style = ttk.Style()
    style.theme_use('clam')
    style.configure('Treeview',  # table row look
                    background=BG2,
                    foreground=TEXT,
                    fieldbackground=BG2,
                    rowheight=30,
                    font=('Helvetica', 11),
                    borderwidth=0)  # no border
    style.configure('Treeview.Heading',  # column header look
                    background=PURPLE_DARK,
                    foreground=TEXT,
                    font=('Helvetica', 10, 'bold'),
                    relief='flat')
    style.map('Treeview',  # when selected look
              background=[('selected', BLUE)],
              foreground=[('selected', TEXT)])

    table = ttk.Treeview(frame,
                         columns=('title', 'rating', 'similarity', 'imdb_id'),
                         show='headings',
                         height=5)
    table.heading('title', text='Title')
    table.heading('rating', text='Avg Rating')
    table.heading('similarity', text='Match')
    table.heading('imdb_id', text='')  # invisible
    table.column('title', width=400)
    table.column('rating', width=100, anchor='center')
    table.column('similarity', width=100, anchor='center')
    table.column('imdb_id', width=0, stretch=False)  # invisible
    table.pack(fill='x')

    return table


def run_app(movies: dict[int, Movie], graph: WeightedGraph) -> None:
    """Creates MovieMatch window.

    Full interface, makes the search button and starts the Tkinter loop.
    """
    window = _setup_window()

    tk.Label(window, text='MovieMatch',
             bg=BG, fg=PURPLE,
             font=('Helvetica', 24, 'bold')).pack(pady=10)

    titles = list(title_to_id(movies).keys())
    search_var = _setup_search(window, titles)
    rating_var = _setup_slider(window)

    current_expanded: dict[str, Optional[str]] = {'iid': None}  # dict of which row has imdb_panel open, starts as None

    def on_row_click(_event: tk.Event) -> None:
        """Open the IMDb page in the web browser when a row is clicked."""
        iid = table.focus()  # return ID of row selected
        if not iid:  # nothing selected
            return
        imdb_id = table.item(iid, 'values')[3]  # gets IMDB ID
        if current_expanded['iid'] == iid:  # if clicked again, do nothing
            current_expanded['iid'] = None
        else:  # build URL and open in browser
            url = f'https://www.imdb.com/title/tt{imdb_id}/'
            webbrowser.open(url)
            current_expanded['iid'] = iid

    def on_search() -> None:  # when search button clicked
        """Run recommendations and update the table and graph."""
        title = search_var.get().strip()
        min_rating = rating_var.get()

        if title not in title_to_id(movies):
            return

        filtered_recs = recommend_with_min_rating(title, graph, movies, min_rating)

        for row in table.get_children():
            table.delete(row)

        current_expanded['iid'] = None

        for movie, score in filtered_recs:
            table.insert('', tk.END, values=(
                movie.title,
                movie.avg_rating,
                f'{round(score * 100)}%',
                movie.imdb_id
            ))

        movie_id = title_to_id(movies)[title]
        input_movie = movies[movie_id]
        graph_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'temp_graph.html')
        fig = build_graph_figure(input_movie, filtered_recs, graph, movies)
        fig.write_html(graph_path)

        graph_label.configure(text='Want to see the graph? Click here!', cursor='hand2')
        graph_label.bind('<Button-1>', lambda e: webbrowser.open(f'file://{graph_path}'))

    btn = tk.Label(window, text='SEARCH',
                   bg=PURPLE_DARK, fg=TEXT,
                   font=('Helvetica', 11, 'bold'),
                   cursor='hand2',
                   padx=20, pady=6)
    btn.pack(pady=10)
    btn.bind('<Button-1>', lambda e: on_search())
    btn.bind('<Enter>', lambda e: btn.configure(bg=PURPLE))
    btn.bind('<Leave>', lambda e: btn.configure(bg=PURPLE_DARK))

    table = _setup_results_table(window)

    graph_label = tk.Label(window, text='',
                           bg=BG, fg=BLUE,
                           font=('Helvetica', 11, 'underline'))
    graph_label.pack(pady=5)

    table.bind('<ButtonRelease-1>', on_row_click)
    window.mainloop()


if __name__ == '__main__':
    import doctest
    doctest.testmod()

    import python_ta

    python_ta.check_all(config={
        'extra-imports': [
            'os', 'webbrowser', 'tkinter', 'tkinter.ttk',
            'data_loader', 'graph', 'recommender', 'visualisations'
        ],
        'allowed-io': ['on_search'],
        'max-line-length': 120,
    })
