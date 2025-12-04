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

@app.route("/orders/user/<int:user_id>", methods=["GET"])
def get_orders_for_user(user_id):
    res = [o for o in ORDERS if o.get("user_id")==user_id]
    return jsonify(res), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003)