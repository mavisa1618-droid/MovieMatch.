from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from recommender import search_movies, recommend_movies


class MovieApp:
    """Tkinter GUI for the movie recommender system."""

    def __init__(self, root: tk.Tk, graph, movies) -> None:
        self._root = root
        self._graph = graph
        self._movies = movies
        self._current_matches = []

        self._root.title('MovieMatch')
        self._root.geometry('900x550')

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

        self._suggestion_listbox = tk.Listbox(root, height=6, width=70)
        self._suggestion_listbox.pack(pady=5)
        self._suggestion_listbox.bind('<<ListboxSelect>>', self._handle_suggestion_click)

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
        """Search for matching movies and display suggestions or recommendations."""
        title = self._title_entry.get()

        self._clear_tree()
        self._suggestion_listbox.delete(0, tk.END)

        matches = search_movies(self._movies, title)
        self._current_matches = matches

        if matches == []:
            self._message_label.config(text='No matching movie found.')
        elif len(matches) == 1:
            self._show_recommendations(matches[0])
        else:
            self._message_label.config(text='Did you mean one of these titles? Click one:')
            for movie in matches[:10]:
                self._suggestion_listbox.insert(tk.END, movie.title)

    def _handle_suggestion_click(self, event) -> None:
        """Handle user clicking one of the suggested titles."""
        selection = self._suggestion_listbox.curselection()

        if selection == ():
            return

        index = selection[0]
        selected_title = self._suggestion_listbox.get(index)

        self._title_entry.delete(0, tk.END)
        self._title_entry.insert(0, selected_title)

        for movie in self._current_matches:
            if movie.title == selected_title:
                self._clear_tree()
                self._show_recommendations(movie)
                break

    def _show_recommendations(self, target_movie) -> None:
        """Display recommendations for a selected movie."""
        min_rating = float(self._rating_scale.get())
        results = recommend_movies(self._graph, target_movie, min_rating)

        self._suggestion_listbox.delete(0, tk.END)

        if results == []:
            self._message_label.config(text=f'No recommendations available for {target_movie.title}.')
        else:
            self._message_label.config(
                text=f'Top {len(results)} recommendations for {target_movie.title}:'
            )
            for result in results:
                self._tree.insert('', 'end', values=result)

    def _clear_tree(self) -> None:
        """Clear all rows in the recommendation table."""
        for item in self._tree.get_children():
            self._tree.delete(item)
