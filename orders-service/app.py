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
        database=os.environ.get("DB_NAME", "capstone"),
    )


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy"}), 200


@app.route("/orders", methods=["GET"])
def list_orders():
    """List all orders"""
    try:
        db = get_db()
        cur = db.cursor(dictionary=True)
        cur.execute(
            """
            SELECT o.id, o.user_id, o.product_id, o.quantity,
                   o.status, o.total_price, o.created_at,
                   u.name as user_name, p.name as product_name
            FROM orders o
            JOIN users u ON o.user_id = u.id
            JOIN products p ON o.product_id = p.id
            ORDER BY o.created_at DESC
            """
        )
        rows = cur.fetchall()
        cur.close()
        db.close()
        return jsonify(rows), 200
    except Error as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/orders", methods=["POST"])
def create_order():
    """Create a new order"""
    payload = request.json
    if not payload or "user_id" not in payload or "product_id" not in payload:
        return jsonify({"error": "Invalid payload. Required: user_id, product_id"}), 400

    user_id = payload["user_id"]
    product_id = payload["product_id"]
    quantity = payload.get("quantity", 1)

    try:
        quantity = int(quantity)
        if quantity < 1:
            return jsonify({"error": "Quantity must be at least 1"}), 400
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid quantity"}), 400

    try:
        db = get_db()
        cur = db.cursor(dictionary=True)

        # Verify user exists
        cur.execute("SELECT id FROM users WHERE id = %s", (user_id,))
        if not cur.fetchone():
            cur.close()
            db.close()
            return jsonify({"error": "User not found"}), 404

        # Verify product exists and get price
        cur.execute("SELECT id, price FROM products WHERE id = %s", (product_id,))
        product = cur.fetchone()
        if not product:
            cur.close()
            db.close()
            return jsonify({"error": "Product not found"}), 404

        # Calculate total price
        total_price = float(product["price"]) * quantity

        # Create order
        cur.execute(
            """
            INSERT INTO orders (user_id, product_id, quantity, status, total_price)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (user_id, product_id, quantity, "created", total_price),
        )
        db.commit()
        order_id = cur.lastrowid

        cur.close()
        db.close()

        return (
            jsonify(
                {
                    "id": order_id,
                    "user_id": user_id,
                    "product_id": product_id,
                    "quantity": quantity,
                    "status": "created",
                    "total_price": total_price,
                    "message": "Order created",
                }
            ),
            201,
        )
    except Error as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/orders/<int:order_id>", methods=["GET"])
def get_order(order_id):
    """Get a specific order"""
    try:
        db = get_db()
        cur = db.cursor(dictionary=True)
        cur.execute(
            """
            SELECT o.id, o.user_id, o.product_id, o.quantity,
                   o.status, o.total_price, o.created_at,
                   u.name as user_name, p.name as product_name
            FROM orders o
            JOIN users u ON o.user_id = u.id
            JOIN products p ON o.product_id = p.id
            WHERE o.id = %s
            """,
            (order_id,),
        )
        row = cur.fetchone()
        cur.close()
        db.close()

        if row:
            return jsonify(row), 200
        return jsonify({"error": "Order not found"}), 404
    except Error as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/orders/user/<int:user_id>", methods=["GET"])
def get_orders_for_user(user_id):
    """Get all orders for a specific user"""
    try:
        db = get_db()
        cur = db.cursor(dictionary=True)
        cur.execute(
            """
            SELECT o.id, o.user_id, o.product_id, o.quantity,
                   o.status, o.total_price, o.created_at,
                   p.name as product_name, p.price as product_price
            FROM orders o
            JOIN products p ON o.product_id = p.id
            WHERE o.user_id = %s
            ORDER BY o.created_at DESC
            """,
            (user_id,),
        )
        rows = cur.fetchall()
        cur.close()
        db.close()
        return jsonify(rows), 200
    except Error as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/orders/<int:order_id>/status", methods=["PUT"])
def update_order_status(order_id):
    """Update order status"""
    payload = request.json
    if not payload or "status" not in payload:
        return jsonify({"error": "Status is required"}), 400

    valid_statuses = ["created", "pending", "processing", "shipped", "delivered", "cancelled"]
    status = payload["status"]

    if status not in valid_statuses:
        return jsonify(
            {"error": f"Invalid status. Valid values: {', '.join(valid_statuses)}"}
        ), 400

    try:
        db = get_db()
        cur = db.cursor()
        cur.execute("UPDATE orders SET status = %s WHERE id = %s", (status, order_id))
        db.commit()

        if cur.rowcount == 0:
            cur.close()
            db.close()
            return jsonify({"error": "Order not found"}), 404

        cur.close()
        db.close()
        return jsonify({"message": "Order status updated", "status": status}), 200
    except Error as exc:
        return jsonify({"error": str(exc)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003, debug=False)
