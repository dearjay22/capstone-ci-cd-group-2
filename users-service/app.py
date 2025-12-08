from flask import Flask, request, jsonify
import os
import mysql.connector

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
    """Health check endpoint"""
    return jsonify({"status": "healthy"}), 200


@app.route("/users", methods=["GET"])
def list_users():
    try:
        db = get_db()
        cur = db.cursor(dictionary=True)

        cur.execute(
            "CREATE TABLE IF NOT EXISTS users ("
            "id INT AUTO_INCREMENT PRIMARY KEY, "
            "name VARCHAR(100), "
            "email VARCHAR(100)"
            ");"
        )

        cur.execute("SELECT id, name, email FROM users LIMIT 100;")
        rows = cur.fetchall()

        cur.close()
        db.close()
        return jsonify(rows), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/users", methods=["POST"])
def create_user():
    payload = request.json

    if not payload or "name" not in payload or "email" not in payload:
        return jsonify({"error": "invalid payload"}), 400

    db = get_db()
    cur = db.cursor()

    cur.execute(
        "INSERT INTO users (name, email) VALUES (%s, %s)",
        (payload["name"], payload["email"]),
    )

    db.commit()
    cur.close()
    db.close()

    return jsonify({"message": "created"}), 201


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
