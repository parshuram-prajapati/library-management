import json
import os
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import messagebox, Listbox, Scrollbar
from PIL import Image, ImageTk

LIBRARY_FILE = "library_gui.json"

# --- Migration helper: update old data to new format ---
def migrate_old_data():
    if os.path.exists(LIBRARY_FILE):
        with open(LIBRARY_FILE, "r") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = {}
        changed = False
        for book_id, book in data.items():
            # If new keys missing, add them
            if "total_copies" not in book or "available_copies" not in book or "issued_copies" not in book:
                # Old data likely had 'copies' meaning total available
                copies = book.get("copies", 1)
                book["total_copies"] = copies
                book["available_copies"] = copies
                # issued_copies list will hold dicts with keys: usn, email, issue_date, due_date
                book["issued_copies"] = []
                # Remove old keys no longer used
                if "copies" in book:
                    del book["copies"]
                if "last_issued" in book:
                    del book["last_issued"]
                if "due_date" in book:
                    del book["due_date"]
                if "issued_to" in book:
                    del book["issued_to"]
                changed = True
        if changed:
            with open(LIBRARY_FILE, "w") as f:
                json.dump(data, f, indent=4)

# Run migration once at start
migrate_old_data()

def load_books():
    try:
        with open(LIBRARY_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}

def save_books(books):
    with open(LIBRARY_FILE, 'w') as f:
        json.dump(books, f, indent=4)

def clear_entries():
    for entry in [id_entry, title_entry, author_entry, copies_entry, usn_entry, email_entry]:
        entry.delete(0, "end")

def add_book():
    book_id = id_entry.get().strip()
    title = title_entry.get().strip()
    author = author_entry.get().strip()
    copies = copies_entry.get().strip()

    if not (book_id and title and author and copies.isdigit() and int(copies) > 0):
        messagebox.showerror("Input Error", "Please fill all fields correctly (copies > 0).")
        return

    books = load_books()
    copies = int(copies)
    if book_id in books:
        # Update total copies and available copies (add new copies)
        books[book_id]["total_copies"] += copies
        books[book_id]["available_copies"] += copies
        messagebox.showinfo("Success", f"Added {copies} more copies to existing book ID {book_id}.")
    else:
        books[book_id] = {
            "title": title,
            "author": author,
            "total_copies": copies,
            "available_copies": copies,
            "issued_copies": []  # list of dicts with keys: usn, email, issue_date, due_date
        }
        messagebox.showinfo("Success", "Book added successfully.")

    save_books(books)
    clear_entries()
    view_books()

def issue_book():
    book_id = id_entry.get().strip()
    usn = usn_entry.get().strip()
    email = email_entry.get().strip()
    if not book_id or not usn or not email:
        messagebox.showerror("Input Error", "Please enter Book ID, USN and Email to issue a book.")
        return

    books = load_books()
    if book_id not in books:
        messagebox.showerror("Error", "Book ID not found.")
        return

    book = books[book_id]
    if book["available_copies"] <= 0:
        messagebox.showerror("Error", "No available copies to issue.")
        return

    # Check if user already issued this book
    for issued in book["issued_copies"]:
        if issued["usn"].lower() == usn.lower():
            messagebox.showerror("Error", f"User {usn} has already issued this book.")
            return

    # Issue book
    issue_date = datetime.now()
    due_date = issue_date + timedelta(days=7)

    book["issued_copies"].append({
        "usn": usn,
        "email": email,
        "issue_date": issue_date.strftime('%Y-%m-%d'),
        "due_date": due_date.strftime('%Y-%m-%d')
    })
    book["available_copies"] -= 1

    save_books(books)
    messagebox.showinfo("Success", f"Book issued to {usn}.\nDue date: {due_date.strftime('%Y-%m-%d')}")
    clear_entries()
    view_books()

def return_book():
    book_id = id_entry.get().strip()
    usn = usn_entry.get().strip()

    if not book_id or not usn:
        messagebox.showerror("Input Error", "Please enter Book ID and USN to return a book.")
        return

    books = load_books()
    if book_id not in books:
        messagebox.showerror("Error", "Book ID not found.")
        return

    book = books[book_id]
    issued_list = book["issued_copies"]

    for issued in issued_list:
        if issued["usn"].lower() == usn.lower():
            # Calculate fine
            issue_date = datetime.strptime(issued["issue_date"], '%Y-%m-%d')
            days_held = (datetime.now() - issue_date).days
            fine = max(0, (days_held - 7) * 10)

            issued_list.remove(issued)
            book["available_copies"] += 1

            save_books(books)
            if fine > 0:
                messagebox.showinfo("Return Info", f"Book returned.\nFine due: ₹{fine}")
            else:
                messagebox.showinfo("Return Info", "Book returned on time. No fine.")
            clear_entries()
            view_books()
            return

    messagebox.showerror("Error", f"No record found of {usn} issuing this book.")

def delete_book():
    book_id = id_entry.get().strip()
    books = load_books()
    if book_id in books:
        confirm = messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete book ID {book_id}?")
        if confirm:
            del books[book_id]
            save_books(books)
            messagebox.showinfo("Deleted", "Book removed successfully.")
            clear_entries()
            view_books()
    else:
        messagebox.showerror("Error", "Book ID not found.")

def view_books():
    book_listbox.delete(0, "end")
    books = load_books()
    if not books:
        book_listbox.insert("end", "No books in library.")
        return

    for book_id, info in sorted(books.items(), key=lambda x: x[1]['title'].lower()):
        base_info = f"{book_id} | {info.get('title','')} by {info.get('author','')} | Total: {info.get('total_copies',0)} | Available: {info.get('available_copies',0)}"
        book_listbox.insert("end", base_info)
        # Show who issued copies
        for issued in info.get("issued_copies", []):
            issued_info = f"   Issued to: {issued['usn']} ({issued['email']}) | Issued: {issued['issue_date']} | Due: {issued['due_date']}"
            book_listbox.insert("end", issued_info)
            # Highlight overdue in red
            try:
                due_date = datetime.strptime(issued['due_date'], '%Y-%m-%d').date()
                if due_date < datetime.now().date():
                    book_listbox.itemconfig("end", {'fg': 'red'})
            except Exception:
                pass

def search_books():
    query = search_entry.get().lower().strip()
    book_listbox.delete(0, "end")
    books = load_books()

    found = False
    for book_id, info in sorted(books.items(), key=lambda x: x[1]['title'].lower()):
        if query in info['title'].lower() or query in info['author'].lower():
            base_info = f"{book_id} | {info.get('title','')} by {info.get('author','')} | Total: {info.get('total_copies',0)} | Available: {info.get('available_copies',0)}"
            book_listbox.insert("end", base_info)
            for issued in info.get("issued_copies", []):
                issued_info = f"   Issued to: {issued['usn']} ({issued['email']}) | Issued: {issued['issue_date']} | Due: {issued['due_date']}"
                book_listbox.insert("end", issued_info)
                try:
                    due_date = datetime.strptime(issued['due_date'], '%Y-%m-%d').date()
                    if due_date < datetime.now().date():
                        book_listbox.itemconfig("end", {'fg': 'red'})
                except Exception:
                    pass
            found = True

    if not found:
        book_listbox.insert("end", "No matching books found.")

def on_book_select(event):
    try:
        selection = book_listbox.get(book_listbox.curselection())
        if "No books" in selection or "No matching" in selection or selection.startswith("   "):
            # Ignore if it's a message or an issued entry
            return
        parts = selection.split(" | ")
        book_id = parts[0].strip()
        books = load_books()
        if book_id in books:
            info = books[book_id]
            id_entry.delete(0, "end")
            id_entry.insert(0, book_id)
            title_entry.delete(0, "end")
            title_entry.insert(0, info.get("title", ""))
            author_entry.delete(0, "end")
            author_entry.insert(0, info.get("author", ""))
            copies_entry.delete(0, "end")
            copies_entry.insert(0, str(info.get("total_copies", 0)))
            # Clear USN and Email since this is just selection
            usn_entry.delete(0, "end")
            email_entry.delete(0, "end")
    except Exception as e:
        print("Selection error:", e)

# UI Setup
app = tk.Tk()
app.title("Library Management System")
app.geometry("900x650")
app.configure(bg="#f0f0f0")

# Title Label
tk.Label(app, text="Library Management System", font=("Segoe UI", 20, "bold"), bg="#003366", fg="white").pack(fill="x", pady=(0, 10))

# Input Frame
frame = tk.Frame(app, bg="#e6e6e6", padx=10, pady=10, relief="groove", bd=2)
frame.pack(padx=20, pady=5, fill="x")

labels = ["Book ID:", "Title:", "Author:", "Copies:", "Issued To (USN):", "Email:"]
entries = []

for i, text in enumerate(labels):
    tk.Label(frame, text=text, bg="#e6e6e6", font=("Segoe UI", 11)).grid(row=i, column=0, sticky="e", padx=5, pady=5)
    entry = tk.Entry(frame, width=45, font=("Segoe UI", 11))
    entry.grid(row=i, column=1, pady=5, padx=5, sticky="w")
    entries.append(entry)

id_entry, title_entry, author_entry, copies_entry, usn_entry, email_entry = entries

# Buttons Frame
btn_frame = tk.Frame(app, bg="#f0f0f0")
btn_frame.pack(pady=10)

buttons = [
    ("Add Book", add_book, "#28a745"),       # green
    ("Issue Book", issue_book, "#ff8800"),   # orange
    ("Return Book", return_book, "#6f42c1"), # purple
    ("Delete Book", delete_book, "#dc3545"), # red
    ("View All", view_books, "#6c757d"),     # grey
]

for i, (text, cmd, color) in enumerate(buttons):
    tk.Button(btn_frame, text=text, command=cmd, bg=color, fg="white", width=15, font=("Segoe UI", 11, "bold")).grid(row=0, column=i, padx=7)

# Search Frame
search_frame = tk.Frame(app, bg="#f0f0f0")
search_frame.pack(pady=10)

search_entry = tk.Entry(search_frame, width=60, font=("Segoe UI", 11))
search_entry.grid(row=0, column=0, padx=5)
tk.Button(search_frame, text="Search", command=search_books, bg="#007bff", fg="white", font=("Segoe UI", 11, "bold"), width=15).grid(row=0, column=1)

# Listbox Frame
frame_list = tk.Frame(app, bg="#f0f0f0")
frame_list.pack(padx=20, pady=10, fill="both", expand=True)

scrollbar = Scrollbar(frame_list)
scrollbar.pack(side="right", fill="y")

book_listbox = Listbox(frame_list, width=110, height=18, font=("Courier New", 11), yscrollcommand=scrollbar.set, selectbackground="#3399ff")
book_listbox.pack(side="left", fill="both", expand=True)

scrollbar.config(command=book_listbox.yview)
book_listbox.bind("<<ListboxSelect>>", on_book_select)

view_books()
app.mainloop()
