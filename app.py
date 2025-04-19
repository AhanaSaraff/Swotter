from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import sqlite3
import base64


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
    try:
        title = request.form['title']
        author = request.form['author']
        category = request.form['category']
        description = request.form['description']
        price = float(request.form['price'])
        condition = request.form['condition']
        images = request.files.getlist('images')

        conn = sqlite3.connect('books.db')
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO books (title, author, category, description, price, condition)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (title, author, category, description, price, condition))

        book_id = cursor.lastrowid

        for image in images:
            blob_data = image.read()
            cursor.execute('''
                INSERT INTO book_images (book_id, image_base64)
                VALUES (?, ?)
            ''', (book_id, blob_data))

        conn.commit()
        conn.close()

        return jsonify({"message": "Book posted successfully!"}), 200

    except Exception as e:
        print("Error:", e)
        return jsonify({"error": "Something went wrong"}), 500

# Display books on home page
@app.route('/api/books')
def get_books():
    conn = sqlite3.connect('books.db')
    cursor = conn.cursor()

    # Get book info with ONE image per book (you can customize this later)
    cursor.execute('''
        SELECT b.id, b.title, b.price, bi.image_base64
        FROM books b
        LEFT JOIN book_images bi ON b.id = bi.book_id
        GROUP BY b.id
    ''')
    
    rows = cursor.fetchall()
    books = []

    for row in rows:
        book_id, title, price, image_blob = row

        if image_blob:
            image_base64 = base64.b64encode(image_blob).decode('utf-8')
            image_url = f"data:image/jpeg;base64,{image_base64}"
        else:
            image_url = None

        books.append({
            'id': book_id,
            'title': title,
            'price': price,
            'image': image_url
        })

    conn.close()
    return jsonify(books)


if __name__ == '__main__':
    app.run(debug=True)
