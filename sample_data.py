
from datetime import date, timedelta
import library
from database import execute, fetch_one

BOOKS = [
 ("Python Crash Course", "Eric Matthes", "Programming", "Hands-on introduction to Python programming with projects"),
 ("Automate the Boring Stuff", "Al Sweigart", "Programming", "Practical Python programming for office automation and scripting"),
 ("Fluent Python", "Luciano Ramalho", "Programming", "Advanced Python features idioms and best practices"),
 ("Clean Code", "Robert C. Martin", "Programming", "Writing readable maintainable software and code craftsmanship"),
 ("The Pragmatic Programmer", "Andrew Hunt", "Programming", "Practical advice for software developers and engineers"),
 ("Introduction to Algorithms", "Thomas Cormen", "Computer Science", "Algorithms data structures and complexity analysis"),
 ("Database System Concepts", "Abraham Silberschatz", "Computer Science", "Relational databases SQL transactions and design"),
 ("Operating System Concepts", "Abraham Silberschatz", "Computer Science", "Processes memory scheduling and file systems"),
 ("Computer Networks", "Andrew Tanenbaum", "Computer Science", "Networking protocols TCP IP and internet architecture"),
 ("Hands-On Machine Learning", "Aurelien Geron", "AI & ML", "Machine learning with scikit-learn Keras and TensorFlow"),
 ("Deep Learning", "Ian Goodfellow", "AI & ML", "Neural networks deep learning theory and practice"),
 ("Pattern Recognition and Machine Learning", "Christopher Bishop", "AI & ML", "Statistical machine learning and probabilistic models"),
 ("Artificial Intelligence: A Modern Approach", "Stuart Russell", "AI & ML", "Complete introduction to artificial intelligence agents and search"),
 ("Python for Data Analysis", "Wes McKinney", "Data Science", "Data analysis with pandas NumPy and Python"),
 ("Data Science from Scratch", "Joel Grus", "Data Science", "Core data science concepts built with Python"),
 ("The Alchemist", "Paulo Coelho", "Fiction", "A shepherd boy journeys to find treasure and his destiny"),
 ("To Kill a Mockingbird", "Harper Lee", "Fiction", "Racial injustice and childhood in the American South"),
 ("1984", "George Orwell", "Fiction", "Dystopian novel about surveillance and totalitarian control"),
 ("Animal Farm", "George Orwell", "Fiction", "Satire of totalitarian politics told through farm animals"),
 ("The Great Gatsby", "F. Scott Fitzgerald", "Fiction", "Wealth love and the American dream in the jazz age"),
 ("Wings of Fire", "A. P. J. Abdul Kalam", "Biography", "Autobiography of India's missile man and president"),
 ("The Story of My Experiments with Truth", "M. K. Gandhi", "Biography", "Gandhi's autobiography on truth and nonviolence"),
 ("Steve Jobs", "Walter Isaacson", "Biography", "Biography of the Apple co-founder and his innovations"),
 ("Sapiens", "Yuval Noah Harari", "History", "A brief history of humankind from ancient times"),
 ("India After Gandhi", "Ramachandra Guha", "History", "History of independent India and its democracy"),
 ("The Discovery of India", "Jawaharlal Nehru", "History", "Nehru's reflection on Indian history and culture"),
 ("Rich Dad Poor Dad", "Robert Kiyosaki", "Finance", "Personal finance lessons on money assets and investing"),
 ("The Intelligent Investor", "Benjamin Graham", "Finance", "Value investing and stock market principles"),
 ("Atomic Habits", "James Clear", "Self Help", "Building good habits and breaking bad ones"),
 ("Deep Work", "Cal Newport", "Self Help", "Focus and productivity in a distracted world"),
 ("A Brief History of Time", "Stephen Hawking", "Science", "Cosmology black holes and the origin of the universe"),
 ("Cosmos", "Carl Sagan", "Science", "Exploring the universe stars and human curiosity"),
 ("Engineering Mathematics", "B. S. Grewal", "Textbook", "Higher engineering mathematics for undergraduate students"),
 ("Let Us C", "Yashavant Kanetkar", "Programming", "Beginner friendly introduction to C programming"),
]
MEMBERS = [("Aarav Sharma","aarav@example.com","9876500001"),("Priya Verma","priya@example.com","9876500002"),
 ("Rohan Gupta","rohan@example.com","9876500003"),("Sneha Singh","sneha@example.com","9876500004"),
 ("Vikram Yadav","vikram@example.com","9876500005"),("Anjali Mishra","anjali@example.com","9876500006"),
 ("Karan Tiwari","karan@example.com","9876500007"),("Neha Srivastava","neha@example.com","9876500008"),
 ("Aditya Pandey","aditya@example.com","9876500009"),("Pooja Dubey","pooja@example.com","9876500010")]

if fetch_one("SELECT COUNT(*) AS n FROM books")["n"] > 0:
    print("Database already has data. Delete library.db to reseed.")
else:
    for i, (t, a, c, d) in enumerate(BOOKS):
        library.add_book(t, a, f"978000{i:05d}", c, 2 + i % 3, d)
    for m in MEMBERS:
        library.add_member(*m)
    # a few demo loans; two are backdated so the Overdue page has data
    for mid, bid in [(1, 1), (2, 10), (3, 16), (4, 24), (5, 6)]:
        library.issue_book(mid, bid)
    old = (date.today() - timedelta(days=20)).isoformat()
    due = (date.today() - timedelta(days=6)).isoformat()
    execute("UPDATE loans SET issue_date=?, due_date=? WHERE loan_id IN (1, 2)", (old, due))
    print(f"Added {len(BOOKS)} books, {len(MEMBERS)} members, 5 loans (2 overdue).")