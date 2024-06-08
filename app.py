

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
from langdetect import detect, DetectorFactory
import wikipediaapi

# To ensure consistent behavior in langdetect
DetectorFactory.seed = 0

app = Flask(__name__)
favorite_books = []

# Initialize the Wikipedia API
wiki_wiki = wikipediaapi.Wikipedia(
    language='en',
    user_agent="visionofdavinci@gmail.com"
)


def search_author(query):
    url = "https://openlibrary.org/search/authors.json"
    params = {"q": query}
    response = requests.get(url, params=params)
    print(f"Author search response: {response.json()}")
    return response.json() if response.status_code == 200 else None

def get_author_works(author_id):
    url = f"https://openlibrary.org/authors/{author_id}/works.json"
    response = requests.get(url)
    print(f"Works response for author {author_id}: {response.json()}")
    return response.json() if response.status_code == 200 else None

def get_publication_year_from_google(title):
    api_key = 'AIzaSyAAbn6S9W4Q11wW66ulPH6N-Y859iXbsSU'  # Replace with your Google Books API Key
    url = f"https://www.googleapis.com/books/v1/volumes?q=intitle:{title}&key={api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data['totalItems'] > 0:
            volume_info = data['items'][0]['volumeInfo']
            return volume_info.get('publishedDate', 'Unknown Year').split("-")[0]
    return 'Unknown Year'

def fetch_wikipedia_data(title):
    page = wiki_wiki.page(title)
    if page.exists():
        description = page.summary[:250]  # First 250 characters of summary
        return description
    return None

def extract_books(works_data, author_name):
    # works = works_data['entries']
    # for work in works:
    #     if 'first_publish_date' not in work:
    #         work['first_publish_date'] = None
    # df = pd.DataFrame(works)
    # print(f"Books DataFrame: {df}")  # Debugging
    # return df[['title', 'first_publish_date']]  # No sorting or filtering

    # works = works_data['entries']
    # book_list = []
    # for work in works:
    #     title = work.get('title', 'Unknown Title')
    #     # Extract the year from 'first_publish_date'
    #     first_publish_date = work.get('first_publish_date', None)
    #     if first_publish_date:
    #         year = first_publish_date.split("-")[0]
    #     else:
    #         # If publication year is missing, fetch from Google Books API
    #         year = get_publication_year_from_google(title)
    #     book_list.append({"title": title, "year": year})

    works = works_data['entries']
    book_list = []
    for work in works:
        title = work.get('title', 'Unknown Title')

        # Only include books authored by the queried author
        first_publish_date = work.get('first_publish_date', None)
        year = first_publish_date.split("-")[0] if first_publish_date else get_publication_year_from_google(title)

        description = fetch_wikipedia_data(title)
        book_list.append({"title": title, "year": year, "description": description})
    
    # Sort books by year, placing 'Unknown Year' at the end
    sorted_books = sorted(book_list, key=lambda x: x['year'] if x['year'] != "Unknown Year" else "9999")
    return sorted_books


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
        if works_data and 'entries' in works_data:
            books = extract_books(works_data, author_name)
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