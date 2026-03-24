from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from recommender import recommend_movies


class MovieApp:
    """Tkinter GUI for the movie recommender system."""

    def __init__(self, root: tk.Tk, graph, movies) -> None:
        self._root = root
        self._graph = graph
        self._movies = movies

        self._root.title('MovieMatch')
        self._root.geometry('900x500')

        title_label = tk.Label(root, text='Enter a movie title:')
        title_label.pack(pady=5)

        self._title_entry = tk.Entry(root, width=50)
        self._title_entry.pack(pady=5)

        rating_label = tk.Label(root, text='Minimum rating:')
        rating_label.pack(pady=5)

        self._rating_scale = tk.Scale(root, from_=0.0, to=5.0, resolution=0.5, orient='horizontal')
        self._rating_scale.set(3.0)
        self._rating_scale.pack(pady=5)

        search_button = tk.Button(root, text='Get Recommendations', command=self._handle_search)
        search_button.pack(pady=10)

        self._message_label = tk.Label(root, text='')
        self._message_label.pack(pady=5)

        self._tree = ttk.Treeview(
            root,
            columns=('Title', 'Average Rating', 'Number of Ratings'),
            show='headings'
        )
        self._tree.heading('Title', text='Title')
        self._tree.heading('Average Rating', text='Average Rating')
        self._tree.heading('Number of Ratings', text='Number of Ratings')

        self._tree.column('Title', width=500)
        self._tree.column('Average Rating', width=120)
        self._tree.column('Number of Ratings', width=140)

        self._tree.pack(fill='both', expand=True, pady=10)

    def _handle_search(self) -> None:
        """Search for movie recommendations and display them."""
        title = self._title_entry.get()
        min_rating = float(self._rating_scale.get())

        for item in self._tree.get_children():
            self._tree.delete(item)

        results = recommend_movies(self._graph, self._movies, title, min_rating)

        if results == []:
            self._message_label.config(text='No matching movie found or no recommendations available.')
        else:
            self._message_label.config(text=f'Top {len(results)} recommendations:')
            for result in results:
                self._tree.insert('', 'end', values=result)
