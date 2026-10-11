import sqlite3
from datetime import date, datetime, timedelta
 
from database import init_db, get_connection, fetch_all, fetch_one
 
LOAN_DAYS = 14
FINE_PER_DAY = 2          # Rs. per late day
MAX_BOOKS_PER_MEMBER = 3
 
init_db()                 # make sure the tables exist when this module loads
 
 

def _today():
    return date.today()
 
 
def _to_date(value):
    """Accept a date object or 'YYYY-MM-DD' text and return a date."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return datetime.strptime(str(value), "%Y-%m-%d").date()
 
 
def add_book(title, author, isbn, category, copies, description=""):
    title, author = (title or "").strip(), (author or "").strip()
    if not title or not author:
        return False, "Title and author are required."
    try:
        copies = int(copies)
    except (TypeError, ValueError):
        return False, "Copies must be a whole number."
    if copies < 1:
        return False, "Copies must be at least 1."
 
    conn = get_connection()
    try:
        conn.execute(
            """INSERT INTO books (title, author, isbn, category, description,
                                  total_copies, available_copies)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (title, author, (isbn or "").strip(), (category or "").strip(),
             (description or "").strip(), copies, copies),
        )
        conn.commit()
        return True, f"Book '{title}' added with {copies} copies."
    except sqlite3.Error as e:
        return False, f"Database error: {e}"
    finally:
        conn.close()
 
 
def search_books(keyword=""):
    """Search title / author / category. Empty keyword returns all books."""
    like = f"%{(keyword or '').strip()}%"
    return fetch_all(
        """SELECT * FROM books
           WHERE title LIKE ? OR author LIKE ? OR category LIKE ?
           ORDER BY title""",
        (like, like, like),
    )
 
 
def delete_book(book_id):
    book = fetch_one("SELECT * FROM books WHERE book_id = ?", (book_id,))
    if not book:
        return False, "Book not found."
    issued = fetch_one(
        "SELECT COUNT(*) AS n FROM loans WHERE book_id = ? AND status = 'issued'",
        (book_id,))["n"]
    if issued:
        return False, f"Cannot delete: {issued} copy(ies) currently issued."
    conn = get_connection()
    try:
        conn.execute("DELETE FROM books WHERE book_id = ?", (book_id,))
        conn.commit()
        return True, f"Book '{book['title']}' deleted."
    except sqlite3.IntegrityError:
        # book has old (returned) loans; we keep history instead of erasing it
        return False, "Cannot delete: this book has borrowing history."
    finally:
        conn.close()
 
 
def update_book(book_id, title, author, isbn, category, description=""):
    """Optional feature: edit book details (stock is not edited here)."""
    if not (title or "").strip() or not (author or "").strip():
        return False, "Title and author are required."
    if not fetch_one("SELECT 1 FROM books WHERE book_id = ?", (book_id,)):
        return False, "Book not found."
    conn = get_connection()
    try:
        conn.execute(
            """UPDATE books SET title=?, author=?, isbn=?, category=?, description=?
               WHERE book_id=?""",
            (title.strip(), author.strip(), isbn, category, description, book_id))
        conn.commit()
        return True, "Book updated."
    finally:
        conn.close()
 
 
# MEMBERS AND LOANS
def add_member(name, email, phone=""):
    name, email = (name or "").strip(), (email or "").strip().lower()
    if not name:
        return False, "Name is required."
    if "@" not in email or "." not in email.split("@")[-1]:
        return False, "Enter a valid email address."
    phone = (phone or "").strip()
    if phone and not (phone.isdigit() and 7 <= len(phone) <= 15):
        return False, "Phone must be 7-15 digits."
 
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO members (name, email, phone, joined_on) VALUES (?, ?, ?, ?)",
            (name, email, phone, _today().isoformat()))
        conn.commit()
        return True, f"Member '{name}' added."
    except sqlite3.IntegrityError:           # UNIQUE(email) in the table
        return False, "A member with this email already exists."
    finally:
        conn.close()
 
 
def list_members():
    return fetch_all("SELECT * FROM members ORDER BY name")
 
 
# ISSUE AND RETURN
def issue_book(member_id, book_id):
    conn = get_connection()
    try:
        member = conn.execute(
            "SELECT * FROM members WHERE member_id = ?", (member_id,)).fetchone()
        book = conn.execute(
            "SELECT * FROM books WHERE book_id = ?", (book_id,)).fetchone()
        if not member:
            return False, "Member not found."
        if not book:
            return False, "Book not found."
        if book["available_copies"] <= 0:
            return False, f"'{book['title']}' has no copies available."
 
        held = conn.execute(
            "SELECT COUNT(*) FROM loans WHERE member_id = ? AND status = 'issued'",
            (member_id,)).fetchone()[0]
        if held >= MAX_BOOKS_PER_MEMBER:
            return False, f"{member['name']} already has {MAX_BOOKS_PER_MEMBER} books."
 
        same = conn.execute(
            """SELECT 1 FROM loans
               WHERE member_id = ? AND book_id = ? AND status = 'issued'""",
            (member_id, book_id)).fetchone()
        if same:
            return False, f"{member['name']} already has this book."
 
        issue = _today()
        due = issue + timedelta(days=LOAN_DAYS)
        # Both changes happen together or not at all (one transaction)
        conn.execute(
            """INSERT INTO loans (member_id, book_id, issue_date, due_date, status)
               VALUES (?, ?, ?, ?, 'issued')""",
            (member_id, book_id, issue.isoformat(), due.isoformat()))
        conn.execute(
            "UPDATE books SET available_copies = available_copies - 1 WHERE book_id = ?",
            (book_id,))
        conn.commit()
        return True, f"Issued '{book['title']}' to {member['name']}. Due on {due}."
    except sqlite3.Error as e:
        conn.rollback()
        return False, f"Database error: {e}"
    finally:
        conn.close()
 
 
def calculate_fine(due_date, return_date):
    """Rs. 2 per late day; never negative."""
    late_days = max(0, (_to_date(return_date) - _to_date(due_date)).days)
    return late_days * FINE_PER_DAY
 
 
def return_book(loan_id):
    conn = get_connection()
    try:
        loan = conn.execute(
            "SELECT * FROM loans WHERE loan_id = ?", (loan_id,)).fetchone()
        if not loan:
            return False, "Loan not found.", 0
        if loan["status"] == "returned":
            return False, "This book was already returned.", 0
 
        today = _today()
        fine = calculate_fine(loan["due_date"], today)
        conn.execute(
            """UPDATE loans SET return_date = ?, fine_amount = ?, status = 'returned'
               WHERE loan_id = ?""", (today.isoformat(), fine, loan_id))
        conn.execute(
            "UPDATE books SET available_copies = available_copies + 1 WHERE book_id = ?",
            (loan["book_id"],))
        conn.commit()
        msg = "Book returned." if fine == 0 else f"Book returned late. Fine: Rs. {fine}."
        return True, msg, fine
    except sqlite3.Error as e:
        conn.rollback()
        return False, f"Database error: {e}", 0
    finally:
        conn.close()
 
 
# REPORTS AND STATS
def get_active_loans():
    """Extra helper for Member B's Return tab (pick an active loan)."""
    return fetch_all(
        """SELECT l.loan_id, m.name AS member, b.title AS book,
                  l.issue_date, l.due_date
           FROM loans l
           JOIN members m ON m.member_id = l.member_id
           JOIN books   b ON b.book_id   = l.book_id
           WHERE l.status = 'issued'
           ORDER BY l.due_date""")
 
 
def get_overdue_books():
    today = _today()
    rows = fetch_all(
        """SELECT l.loan_id, m.name AS member, b.title AS book, l.due_date
           FROM loans l
           JOIN members m ON m.member_id = l.member_id
           JOIN books   b ON b.book_id   = l.book_id
           WHERE l.status = 'issued' AND l.due_date < ?
           ORDER BY l.due_date""", (today.isoformat(),))
    for r in rows:
        r["days_late"] = (today - _to_date(r["due_date"])).days
        r["fine_so_far"] = calculate_fine(r["due_date"], today)
    return rows
 
 
def get_member_history(member_id):
    """Optional feature: borrowing history of one member."""
    return fetch_all(
        """SELECT l.loan_id, b.title AS book, l.issue_date, l.due_date,
                  l.return_date, l.fine_amount, l.status
           FROM loans l JOIN books b ON b.book_id = l.book_id
           WHERE l.member_id = ? ORDER BY l.issue_date DESC""", (member_id,))
 
 
def get_stats():
    books = fetch_one("SELECT COALESCE(SUM(total_copies), 0) AS n FROM books")["n"]
    issued = fetch_one(
        "SELECT COUNT(*) AS n FROM loans WHERE status = 'issued'")["n"]
    members = fetch_one("SELECT COUNT(*) AS n FROM members")["n"]
    return {"total_books": books, "issued": issued,
            "overdue": len(get_overdue_books()), "members": members}
 
 
def get_books_by_category():
    """For the dashboard bar chart: {category: number_of_titles}."""
    rows = fetch_all(
        """SELECT COALESCE(NULLIF(category, ''), 'Other') AS category,
                  COUNT(*) AS n FROM books GROUP BY 1 ORDER BY n DESC""")
    return {r["category"]: r["n"] for r in rows}
 
 
def export_loans_csv():
    """Optional feature: all loans as CSV text (for st.download_button)."""
    import csv, io
    rows = fetch_all(
        """SELECT l.loan_id, m.name AS member, b.title AS book, l.issue_date,
                  l.due_date, l.return_date, l.fine_amount, l.status
           FROM loans l JOIN members m ON m.member_id = l.member_id
                        JOIN books b ON b.book_id = l.book_id
           ORDER BY l.loan_id""")
    out = io.StringIO()
    if rows:
        w = csv.DictWriter(out, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)
    return out.getvalue()
 
 
# --------------------------------------------------------------- optional AI
# def get_similar_books(book_id):
#     from recommender import similar_books      # imported only when needed
#     return similar_books(book_id, top_n=5)
 