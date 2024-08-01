import sqlite3
from flask import Flask, jsonify, request, g, abort
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app, origins=["http://127.0.0.1:5500"])

DATABASE = 'products.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS products
                          (id INTEGER PRIMARY KEY,
                           name TEXT NOT NULL,
                           image_url TEXT,
                           description TEXT,
                           stock_items INTEGER NOT NULL,
                           price REAL NOT NULL,
                           category TEXT)''')
        db.commit()

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route('/products', methods=['GET'])
def get_all_products():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM products')
    products = cursor.fetchall()
    products_list = [{'id': row[0], 'name': row[1], 'image_url': row[2], 'description': row[3], 'stock_items': row[4], 'price': row[5], 'category': row[6]} for row in products]
    return jsonify({'products': products_list})


@app.route('/add_new_products', methods=['POST'])
def add_product():
    if not request.json or not 'name' in request.json or not 'stock_items' in request.json or not 'price' in request.json:
        abort(400)
    
    data = request.json
    name = data['name']
    url = data.get('image_url', '')
    description = data.get('description', '')
    stock_items = data['stock_items']
    price = data['price']
    category = data['category']
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''INSERT INTO products (name, image_url, description, stock_items, price, category)
                      VALUES (?, ?, ?, ?, ?, ?)''',
                   (name, url, description, stock_items, price, category))
    db.commit()
    
    new_product_id = cursor.lastrowid
    new_product = {'id': new_product_id, 'name': name, 'image_url': url, 'description': description, 'stock_items': stock_items, 'price': price, 'category': category}
    
    return jsonify({'product': new_product}), 201

@app.route('/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM products WHERE id = ?', (product_id,))
        product = cursor.fetchone()
        if product is None:
            abort(404)
        
        cursor.execute('DELETE FROM products WHERE id = ?', (product_id,))
        db.commit()
        
        deleted_product = {'id': product_id, 'name': product[1], 'image_url': product[2], 'description': product[3], 'stock_items': product[4], 'price': product[5], 'category': product[6]}
        return jsonify({'product': deleted_product})

@app.route('/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM products WHERE id = ?', (product_id,))
    product = cursor.fetchone()
    if product is None:
        abort(404)
    
    if not request.json:
        abort(400)
    
    data = request.json
    name = data.get('name', product[1])
    url = data.get('image_url', product[2])
    description = data.get('description', product[3])
    stock_items = data.get('stock_items', product[4])
    price = data.get('price', product[5])
    category = data.get('category', product[6])
    
    cursor.execute('''UPDATE products SET name = ?, image_url = ?, description = ?, stock_items = ?, price = ?, category = ?
                  WHERE id = ?''',
               (name, url, description, stock_items, price, category, product_id))

    db.commit()
    updated_product = {'id': product_id, 'name': name, 'image_url': url, 'description': description, 'stock_items': stock_items, 'price': price, 'category': category}
    return jsonify({'product': updated_product})

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Bad request'}), 400

if __name__ == '__main__':
    init_db()
    app.run(debug=False, port=5000)
    
