import json
import os
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import messagebox, Listbox, Scrollbar
from PIL import Image, ImageTk

LIBRARY_FILE = "library_gui.json"

if not os.path.exists(LIBRARY_FILE):
    with open(LIBRARY_FILE, 'w') as f:
        json.dump({}, f)

def load_books():
    try:
        with open(LIBRARY_FILE, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

def save_books(books):
    with open(LIBRARY_FILE, 'w') as f:
        json.dump(books, f, indent=4)

def clear_entries():
    for entry in [id_entry, title_entry, author_entry, copies_entry, usn_entry]:
        entry.delete(0, "end")

def add_book():
    book_id = id_entry.get()
    title = title_entry.get()
    author = author_entry.get()
    copies = copies_entry.get()

    if not (book_id and title and author and copies.isdigit()):
        messagebox.showerror("Input Error", "Please fill all fields correctly.")
        return

    books = load_books()
    if book_id in books:
        messagebox.showerror("Error", "Book ID already exists.")
    else:
        books[book_id] = {
            "title": title,
            "author": author,
            "copies": int(copies),
            "last_issued": None,
            "due_date": None,
            "issued_to": None
        }
        save_books(books)
        messagebox.showinfo("Success", "Book added successfully.")
        clear_entries()
        view_books()

def issue_book():
    book_id = id_entry.get()
    usn = usn_entry.get().strip()
    if not usn:
        messagebox.showerror("Input Error", "Please enter the USN of the person issuing the book.")
        return

    books = load_books()
    if book_id in books and books[book_id]['copies'] > 0:
        if books[book_id]['issued_to']:
            messagebox.showerror("Error", f"Book already issued to {books[book_id]['issued_to']}.")
            return
        books[book_id]['copies'] -= 1
        books[book_id]['last_issued'] = datetime.now().strftime('%Y-%m-%d')
        books[book_id]['due_date'] = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        books[book_id]['issued_to'] = usn
        save_books(books)
        messagebox.showinfo("Success", f"Book issued successfully to {usn}!\nDue Date: {books[book_id]['due_date']}")
        clear_entries()
        view_books()
    else:
        messagebox.showerror("Error", "Book not available or ID incorrect.")

def return_book():
    book_id = id_entry.get()
    books = load_books()
    if book_id in books:
        if not books[book_id]['issued_to']:
            messagebox.showinfo("Return Info", "This book is not currently issued.")
            return
        books[book_id]['copies'] += 1
        issue_date_str = books[book_id].get('last_issued')
        if issue_date_str:
            issue_date = datetime.strptime(issue_date_str, '%Y-%m-%d')
            days_held = (datetime.now() - issue_date).days
            fine = (days_held - 7) * 10 if days_held > 7 else 0
            if fine > 0:
                messagebox.showinfo("Return Info", f"Book returned.\nFine due: ₹{fine}")
            else:
                messagebox.showinfo("Return Info", "Book returned on time. No fine.")
        books[book_id]['last_issued'] = None
        books[book_id]['due_date'] = None
        books[book_id]['issued_to'] = None
        save_books(books)
        clear_entries()
        view_books()
    else:
        messagebox.showerror("Error", "Invalid Book ID.")

def delete_book():
    book_id = id_entry.get()
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
        display = f"{book_id} | {info['title']} by {info['author']} | Copies: {info['copies']}"
        if info.get('last_issued') and info.get('issued_to'):
            display += f" | Issued on: {info['last_issued']} to {info['issued_to']}"
        if info.get('due_date'):
            display += f" | Due: {info['due_date']}"
        book_listbox.insert("end", display)
        # Highlight overdue books in red
        if info.get('due_date'):
            try:
                due_date = datetime.strptime(info['due_date'], '%Y-%m-%d').date()
                if due_date < datetime.now().date():
                    book_listbox.itemconfig("end", {'fg': 'red'})
            except Exception:
                pass

def search_books():
    query = search_entry.get().lower()
    book_listbox.delete(0, "end")
    books = load_books()
    for book_id, info in sorted(books.items(), key=lambda x: x[1]['title'].lower()):
        if query in info['title'].lower() or query in info['author'].lower():
            display = f"{book_id} | {info['title']} by {info['author']} | Copies: {info['copies']}"
            if info.get('last_issued') and info.get('issued_to'):
                display += f" | Issued on: {info['last_issued']} to {info['issued_to']}"
            if info.get('due_date'):
                display += f" | Due: {info['due_date']}"
            book_listbox.insert("end", display)
            if info.get('due_date'):
                try:
                    due_date = datetime.strptime(info['due_date'], '%Y-%m-%d').date()
                    if due_date < datetime.now().date():
                        book_listbox.itemconfig("end", {'fg': 'red'})
                except Exception:
                    pass
    if book_listbox.size() == 0:
        book_listbox.insert("end", "No matching books found.")

def on_book_select(event):
    try:
        selection = book_listbox.get(book_listbox.curselection())
        if "No books" in selection or "No matching" in selection:
            return
        parts = selection.split(" | ")
        book_id = parts[0]
        books = load_books()
        if book_id in books:
            info = books[book_id]
            id_entry.delete(0, "end")
            id_entry.insert(0, book_id)
            title_entry.delete(0, "end")
            title_entry.insert(0, info["title"])
            author_entry.delete(0, "end")
            author_entry.insert(0, info["author"])
            copies_entry.delete(0, "end")
            copies_entry.insert(0, str(info["copies"]))
            usn_entry.delete(0, "end")
            if info.get("issued_to"):
                usn_entry.insert(0, info["issued_to"])
            else:
                usn_entry.insert(0, "")
    except Exception as e:
        print("Selection error:", e)

# UI Setup
app = tk.Tk()
app.title("Library Management System")
app.geometry("850x620")

# Background
try:
    bg_image = Image.open("background.jpg")
    bg_photo = ImageTk.PhotoImage(bg_image.resize((850, 620)))
    bg_label = tk.Label(app, image=bg_photo)
    bg_label.place(x=0, y=0, relwidth=1, relheight=1)
except:
    app.configure(bg="#f5f5f5")

tk.Label(app, text="Library Management System", font=("Segoe UI", 18, "bold"), bg="#003366", fg="white").pack(fill="x")

frame = tk.Frame(app, bg="lightgrey")
frame.pack(pady=10)

labels = ["Book ID:", "Title:", "Author:", "Copies:", "Issued To (USN):"]
entries = []
for i, text in enumerate(labels):
    tk.Label(frame, text=text, bg="lightgrey").grid(row=i, column=0, sticky="e", padx=5, pady=2)
    entry = tk.Entry(frame, width=40)
    entry.grid(row=i, column=1, pady=2)
    entries.append(entry)

id_entry, title_entry, author_entry, copies_entry, usn_entry = entries

btn_frame = tk.Frame(app, bg="white")
btn_frame.pack(pady=10)

buttons = [
    ("Add Book", add_book, "green"),
    ("Issue Book", issue_book, "orange"),
    ("Return Book", return_book, "purple"),
    ("Delete Book", delete_book, "red"),
    ("View All", view_books, "grey"),
]

for i, (text, cmd, color) in enumerate(buttons):
    tk.Button(btn_frame, text=text, command=cmd, bg=color, fg="white", width=15).grid(row=0, column=i, padx=5)

search_frame = tk.Frame(app)
search_frame.pack(pady=5)

search_entry = tk.Entry(search_frame, width=50)
search_entry.grid(row=0, column=0)
tk.Button(search_frame, text="Search", command=search_books).grid(row=0, column=1, padx=5)

frame_list = tk.Frame(app)
frame_list.pack(pady=10)

scrollbar = Scrollbar(frame_list)
scrollbar.pack(side="right", fill="y")

book_listbox = Listbox(frame_list, width=100, height=15, font=("Courier New", 10), yscrollcommand=scrollbar.set)
book_listbox.pack(side="left", fill="both")

scrollbar.config(command=book_listbox.yview)
book_listbox.bind("<<ListboxSelect>>", on_book_select)

view_books()
app.mainloop()
