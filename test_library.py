from datetime import date, timedelta
import pytest
import database
import library
 
 
@pytest.fixture(autouse=True)
def fresh_db(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "test.db")
    database.init_db()
 
 
def _setup(copies=1):
    library.add_book("Test Book", "Author", "111", "Demo", copies)
    library.add_member("Alice", "alice@x.com", "9999999999")
    return 1, 1   # member_id, book_id
 
 
def test_issue_reduces_available_copies():
    m, b = _setup(copies=2)
    ok, _ = library.issue_book(m, b)
    assert ok and library.search_books("Test")[0]["available_copies"] == 1
 
 
def test_cannot_issue_unavailable_book():
    m, b = _setup(copies=1)
    library.add_member("Bob", "bob@x.com", "")
    library.issue_book(m, b)
    ok, msg = library.issue_book(2, b)
    assert not ok and "no copies" in msg
 
 
def test_three_book_limit():
    m, _ = _setup()
    for i in range(2, 6):
        library.add_book(f"Book {i}", "A", "", "", 1)
    results = [library.issue_book(m, b)[0] for b in (1, 2, 3, 4)]
    assert results == [True, True, True, False]
 
 
def test_fine_calculation():
    assert library.calculate_fine("2026-01-01", "2026-01-01") == 0
    assert library.calculate_fine("2026-01-10", "2026-01-05") == 0
    assert library.calculate_fine("2026-01-01", "2026-01-06") == 10
 
 
def test_return_restores_copy_and_marks_returned():
    m, b = _setup()
    library.issue_book(m, b)
    ok, _, fine = library.return_book(1)
    assert ok and fine == 0
    assert library.search_books("Test")[0]["available_copies"] == 1
    assert not library.return_book(1)[0]          # cannot return twice
 
 
def test_overdue_fine_on_return():
    m, b = _setup()
    library.issue_book(m, b)
    late = (date.today() - timedelta(days=3)).isoformat()
    database.execute("UPDATE loans SET due_date = ? WHERE loan_id = 1", (late,))
    assert library.get_overdue_books()[0]["days_late"] == 3
    assert library.return_book(1)[2] == 6
 
 
def test_duplicate_email_blocked():
    assert library.add_member("A", "a@x.com", "")[0]
    assert not library.add_member("B", "A@X.com", "")[0]
 
 
def test_cannot_delete_issued_book():
    m, b = _setup()
    library.issue_book(m, b)
    assert not library.delete_book(b)[0]
 
 
def test_bad_input_does_not_crash():
    assert not library.add_book("", "x", "", "", 1)[0]
    assert not library.add_book("T", "A", "", "", "abc")[0]
    assert not library.add_member("X", "not-an-email", "")[0]
    assert not library.issue_book(999, 999)[0]
 