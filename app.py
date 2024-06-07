

# import time
# from watchdog.observers import Observer
# from watchdog.events import FileSystemEventHandler

# class FileEventHandler(FileSystemEventHandler):
#     def on_modified(self, event):
#         print(f'{event.src_path} has been modified')

#     def on_created(self, event):
#         print(f'{event.src_path} has been created')

#     def on_deleted(self, event):
#         print(f'{event.src_path} has been deleted')

# if __name__ == "__main__":
#     path = "."  # Watch the current directory
#     event_handler = FileEventHandler()
#     observer = Observer()
#     observer.schedule(event_handler, path, recursive=True)
#     observer.start()

#     try:
#         while True:
#             time.sleep(1)
#     except KeyboardInterrupt:
#         observer.stop()

#     observer.join()



from flask import Flask, render_template, request
import requests
import pandas as pd

app = Flask(__name__)
favorite_books = []

def search_author(query):
    url = "https://openlibrary.org/search/authors.json"
    params = {"q": query}
    response = requests.get(url, params=params)
    return response.json() if response.status_code == 200 else None

def get_author_works(author_id):
    url = f"https://openlibrary.org/authors/{author_id}/works.json"
    response = requests.get(url)
    return response.json() if response.status_code == 200 else None

def create_timeline(works_data):
    works = works_data['entries']
    for work in works:
        if 'first_publish_date' not in work:
            work['first_publish_date'] = None
    df = pd.DataFrame(works)
    df['publication_date'] = pd.to_datetime(df['first_publish_date'], errors='coerce')
    df = df.dropna(subset=['publication_date']).sort_values(by='publication_date').reset_index(drop=True)
    return df[['title', 'publication_date']]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    author_name = request.form.get('author_name')
    authors = search_author(author_name)
    
    if authors and 'docs' in authors and authors['docs']:
        author_id = authors['docs'][0]['key'].split('/')[-1]
        
        # Get works by author
        works_data = get_author_works(author_id)
        if works_data:
            timeline_df = create_timeline(works_data)
            books = timeline_df.to_dict('records')
            return render_template('books.html', books=books, author_name=author_name)
        else:
            return "No works found for the author."
    else:
        return "Author not found."

@app.route('/add_favorite', methods=['POST'])
def add_favorite():
    book_title = request.form.get('book_title')
    if book_title not in favorite_books:
        favorite_books.append(book_title)
    return '', 204

@app.route('/favorites')
def favorites():
    return render_template('favorites.html', favorite_books=favorite_books)

if __name__ == "__main__":
    app.run(debug=True)