from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import sqlite3

app = Flask(__name__)
CORS(app)

# DB setup
def init_db():
    conn = sqlite3.connect('books.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            author TEXT,
            category TEXT,
            description TEXT,
            price REAL,
            condition TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS book_images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id INTEGER,
            image_base64 TEXT,
            FOREIGN KEY (book_id) REFERENCES books(id)
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Endpoint to receive book data
@app.route('/api/books', methods=['POST'])
def add_book():
    data = request.json
    try:
        conn = sqlite3.connect('books.db')
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO books (title, author, category, description, price, condition)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (data['title'], data['author'], data['category'],
              data['description'], float(data['price']), data['condition']))

        book_id = cursor.lastrowid

        for img_base64 in data.get('images', []):
            cursor.execute('''
                INSERT INTO book_images (book_id, image_base64)
                VALUES (?, ?)
            ''', (book_id, img_base64))

        conn.commit()
        conn.close()

        return jsonify({"message": "Book posted successfully!"}), 200

    except Exception as e:
        print("Error:", e)
        return jsonify({"error": "Something went wrong"}), 500

# Display books on home page
@app.route('/')
def home():
    conn = sqlite3.connect('books.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT b.id, b.title, b.author, b.category, b.description, b.price, b.condition,
               (SELECT image_base64 FROM book_images WHERE book_id = b.id LIMIT 1)
        FROM books b
    ''')
    books = cursor.fetchall()
    conn.close()

    books_list = []
    for book in books:
        print("Fetched Book:", book)
        books_list.append({
            'id': book[0],
            'title': book[1],
            'author': book[2],
            'category': book[3],
            'description': book[4],
            'price': book[5],
            'condition': book[6],
            'image': book[7]  # base64 image string
        })

    return render_template('index.html', books=books_list)

@app.route('/api/books/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):
    try:
        conn = sqlite3.connect('books.db')
        cursor = conn.cursor()
        
        # Delete from book_images first (foreign key)
        cursor.execute('DELETE FROM book_images WHERE book_id = ?', (book_id,))
        # Then delete the book
        cursor.execute('DELETE FROM books WHERE id = ?', (book_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({"message": "Book deleted successfully."}), 200

    except Exception as e:
        print("Delete Error:", e)
        return jsonify({"error": "Failed to delete book."}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)
