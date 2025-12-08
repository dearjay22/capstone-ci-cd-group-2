from flask import Flask, jsonify, request
import os
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)


def get_db():
    """Create database connection."""
    return mysql.connector.connect(
        host=os.environ.get("DB_HOST", "mysql"),
        user=os.environ.get("DB_USER", "root"),
        password=os.environ.get("DB_PASS", "rootpass"),
        database=os.environ.get("DB_NAME", "capstone"),
    )


def fetch_products():
    """Return all products as a list of dicts."""
    db = get_db()
    cur = db.cursor(dictionary=True)
    try:
        cur.execute(
            "SELECT id, name, price, description, created_at "
            "FROM products ORDER BY id"
        )
        rows = cur.fetchall()
        return rows
    finally:
        cur.close()
        db.close()


def fetch_product(product_id: int):
    """Return a single product dict or None if not found."""
    db = get_db()
    cur = db.cursor(dictionary=True)
    try:
        cur.execute(
            "SELECT id, name, price, description, created_at "
            "FROM products WHERE id = %s",
            (product_id,),
        )
        row = cur.fetchone()
        return row
    finally:
        cur.close()
        db.close()


def create_product(data: dict):
    """
    Create a product in the DB and return its data.

    Expected keys in data:
      - name (required)
      - price (optional, defaults to 0.0)
      - description (optional, defaults to "")
    """
    name = data["name"]
    price = data.get("price", 0.0)
    description = data.get("description", "")

    db = get_db()
    cur = db.cursor()
    try:
        cur.execute(
            "INSERT INTO products (name, price, description) VALUES (%s, %s, %s)",
            (name, price, description),
        )
        db.commit()
        product_id = cur.lastrowid
        return {
            "id": product_id,
            "name": name,
            "price": price,
            "description": description,
        }
    finally:
        cur.close()
        db.close()


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy"}), 200


@app.route("/products", methods=["GET"])
def list_products():
    """List all products from database."""
    try:
        products = fetch_products()
        return jsonify(products), 200
    except Error as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/products/<int:product_id>", methods=["GET"])
def get_product(product_id):
    """Get a specific product by ID."""
    try:
        product = fetch_product(product_id)
        if product:
            return jsonify(product), 200
        return jsonify({"error": "Product not found"}), 404
    except Error as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/products", methods=["POST"])
def add_product():
    """
    Add a new product to database.

    Tests monkeypatch app.create_product, so this route MUST call create_product().
    Name is required; price/description are optional.
    """
    payload = request.get_json() or {}

    if "name" not in payload:
        return jsonify({"error": "Invalid payload. Required: name"}), 400

    # Optional fields with defaults
    price = payload.get("price", 0.0)
    description = payload.get("description", "")

    # Basic validation when price is provided
    if "price" in payload:
        try:
            price = float(price)
            if price < 0:
                return jsonify({"error": "Price must be positive"}), 400
        except (ValueError, TypeError):
            return jsonify({"error": "Price must be a valid number"}), 400

    try:
        product = create_product(
            {
                "name": payload["name"],
                "price": price,
                "description": description,
            }
        )
        return jsonify(product), 201
    except Error as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/products/<int:product_id>", methods=["PUT"])
def update_product(product_id):
    """Update an existing product."""
    payload = request.get_json() or {}
    if not payload:
        return jsonify({"error": "No data provided"}), 400

    updates = []
    values = []

    if "name" in payload:
        updates.append("name = %s")
        values.append(payload["name"])

    if "price" in payload:
        try:
            price = float(payload["price"])
        except (ValueError, TypeError):
            return jsonify({"error": "Price must be a valid number"}), 400
        updates.append("price = %s")
        values.append(price)

    if "description" in payload:
        updates.append("description = %s")
        values.append(payload["description"])

    if not updates:
        return jsonify({"error": "No valid fields to update"}), 400

    values.append(product_id)

    try:
        db = get_db()
        cur = db.cursor()
        query = "UPDATE products SET " + ", ".join(updates) + " WHERE id = %s"
        cur.execute(query, values)
        db.commit()

        if cur.rowcount == 0:
            cur.close()
            db.close()
            return jsonify({"error": "Product not found"}), 404

        cur.close()
        db.close()
        return jsonify({"message": "Product updated"}), 200
    except Error as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/products/<int:product_id>", methods=["DELETE"])
def delete_product(product_id):
    """Delete a product."""
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
    except Error as exc:
        return jsonify({"error": str(exc)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=False)
