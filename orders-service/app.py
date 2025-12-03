from flask import Flask, jsonify, request
app = Flask(__name__)
ORDERS = []

@app.route("/orders", methods=["POST"])
def create_order():
    o = request.json
    if not o or "user_id" not in o or "product_id" not in o:
        return jsonify({"error":"invalid"}), 400
    o["id"] = len(ORDERS) + 1
    o["status"] = "created"
    ORDERS.append(o)
    return jsonify(o), 201