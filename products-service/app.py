from flask import Flask, jsonify, request
import os
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)

def get_db():
    """Create database connection"""
    return mysql.connector.connect(
        host=os.environ.get("DB_HOST", "mysql"),
        user=os.environ.get("DB_USER", "root"),
        password=os.environ.get("DB_PASS", "rootpass"),
        database=os.environ.get("DB_NAME", "capstone")
    )

@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy"}), 200

@app.route("/products", methods=["GET"])
def list_products():
    """List all products from database"""
    try:
        db = get_db()
        cur = db.cursor(dictionary=True)
        cur.execute("SELECT id, name, price, description, created_at FROM products ORDER BY id")
        rows = cur.fetchall()
        cur.close()
        db.close()
        return jsonify(rows), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500

@app.route("/products/<int:product_id>", methods=["GET"])
def get_product(product_id):
    """Get a specific product by ID"""
    try:
        db = get_db()
        cur = db.cursor(dictionary=True)
        cur.execute("SELECT id, name, price, description, created_at FROM products WHERE id = %s", (product_id,))
        row = cur.fetchone()
        cur.close()
        db.close()
        if row:
            return jsonify(row), 200
        return jsonify({"error": "Product not found"}), 404
    except Error as e:
        return jsonify({"error": str(e)}), 500

@app.route("/products", methods=["POST"])
def add_product():
    """Add a new product to database"""
    payload = request.json
    if not payload or "name" not in payload or "price" not in payload:
        return jsonify({"error": "Invalid payload. Required: name, price"}), 400
    
    try:
        price = float(payload["price"])
        if price < 0:
            return jsonify({"error": "Price must be positive"}), 400
    except ValueError:
        return jsonify({"error": "Price must be a valid number"}), 400
    
    try:
        db = get_db()
        cur = db.cursor()
        cur.execute(
            "INSERT INTO products (name, price, description) VALUES (%s, %s, %s)",
            (payload["name"], price, payload.get("description", ""))
        )
        db.commit()
        product_id = cur.lastrowid
        cur.close()
        db.close()
        return jsonify({"id": product_id, "message": "Product created"}), 201
    except Error as e:
        return jsonify({"error": str(e)}), 500

@app.route("/products/<int:product_id>", methods=["PUT"])
def update_product(product_id):
    """Update an existing product"""
    payload = request.json
    if not payload:
        return jsonify({"error": "No data provided"}), 400
    
    try:
        db = get_db()
        cur = db.cursor()
        
        # Build dynamic update query
        updates = []
        values = []
        if "name" in payload:
            updates.append("name = %s")
            values.append(payload["name"])
        if "price" in payload:
            updates.append("price = %s")
            values.append(float(payload["price"]))
        if "description" in payload:
            updates.append("description = %s")
            values.append(payload["description"])
        
        if not updates:
            return jsonify({"error": "No valid fields to update"}), 400
        
        values.append(product_id)
        query = f"UPDATE products SET {', '.join(updates)} WHERE id = %s"
        cur.execute(query, values)
        db.commit()
        
        if cur.rowcount == 0:
            cur.close()
            db.close()
            return jsonify({"error": "Product not found"}), 404
        
        cur.close()
        db.close()
        return jsonify({"message": "Product updated"}), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500

@app.route("/products/<int:product_id>", methods=["DELETE"])
def delete_product(product_id):
    """Delete a product"""
    try:
        db = get_db()
        cur = db.cursor()
        cur.execute("DELETE FROM products WHERE id = %s", (product_id,))
        db.commit()
        
        if cur.rowcount == 0:
            cur.close()
            db.close()
            return jsonify({"error": "Product not found"}), 404
        
        cur.close()
        db.close()
        return jsonify({"message": "Product deleted"}), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=False)
