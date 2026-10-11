from database import fetch_all
 
 
def similar_books(book_id, top_n=5):
    books = fetch_all("SELECT * FROM books ORDER BY book_id")
    ids = [b["book_id"] for b in books]
    if book_id not in ids or len(books) < 2:
        return []
 
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
    except ImportError:
        return []                      # scikit-learn missing: feature off, app still works
 
    # One text blob per book: title + author + category + description
    texts = [f"{b['title']} {b['author']} {b['category']} {b['description']}"
             for b in books]
    matrix = TfidfVectorizer(stop_words="english").fit_transform(texts)
 
    pos = ids.index(book_id)
    scores = cosine_similarity(matrix[pos], matrix).flatten()
    scores[pos] = -1                   # do not recommend the book itself
 
    best = scores.argsort()[::-1][:top_n]
    return [{**books[i], "similarity": round(float(scores[i]), 3)}
            for i in best if scores[i] > 0]
 