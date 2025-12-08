from flask import Flask, jsonify, request
import os
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)


def get_db():
    return mysql.connector.connect(
        host=os.environ.get("DB_HOST", "mysql"),
        user=os.environ.get("DB_USER", "root"),
        password=os.environ.get("DB_PASS", "rootpass"),
        database=os.environ.get("DB_NAME", "capstone"),
    )


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy"}), 200


@app.route("/products", methods=["GET"])
def list_products():
    try:
        db = get_db()
        cur = db.cursor(dictionary=True)
        cur.execute("SELECT id, name, price, description, created_at FROM products ORDER BY id")
        rows = cur.fetchall()
        cur.close()
        db.close()
        return jsonify(rows), 200
    except Error as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/products/<int:product_id>", methods=["GET"])
def get_product(product_id):
    try:
        db = get_db()
        cur = db.cursor(dictionary=True)
        cur.execute(
            "SELECT id, name, price, description, created_at FROM products WHERE id = %s",
            (product_id,),
        )
        row = cur.fetchone()
        cur.close()
        db.close()
        if row:
            return jsonify(row), 200
        return jsonify({"error": "Product not found"}), 404
    except Error as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/products", methods=["POST"])
def add_product():
    payload = request.json
    if not payload or "name" not in payload or "price" not in payload:
        return jsonify({"error": "Invalid payload. Required: name, price"}), 400

    try:
        price = float(payload["price"])
        if price < 0:
            return jsonify({"error": "Price must be positive"}), 400
    except (ValueError, TypeError):
        return jsonify({"error": "Price must be a valid number"}), 400

    try:
        db = get_db()
        cur = db.cursor()
        cur.execute(
            "INSERT INTO products (name, price, description) VALUES (%s, %s, %s)",
            (payload["name"], price, payload.get("description", "")),
        )
        db.commit()
        product_id = cur.lastrowid
        cur.close()
        db.close()
        return jsonify({"id": product_id, "message": "Product created"}), 201
    except Error as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/products/<int:product_id>", methods=["PUT"])
def update_product(product_id):
    payload = request.json
    if not payload:
        return jsonify({"error": "No data provided"}), 400

    allowed_fields = {"name", "price, description"}

    updates = []
    values = []

    for field, value in payload.items():
        if field in allowed_fields:
            updates.append(f"{field} = %s")
            if field == "price":
                value = float(value)
            values.append(value)

    if not updates:
        return jsonify({"error": "No valid fields to update"}), 400

    values.append(product_id)

    try:
        db = get_db()
        cur = db.cursor()

        # FIXED: This is now safe from SQL injection
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
    except Error as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/products/<int:product_id>", methods=["DELETE"])
def delete_product(product_id):
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
