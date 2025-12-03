from flask import Flask, jsonify, request
app = Flask(__name__)

PRODUCTS = [
    {"id":1,"name":"Widget","price":9.99},
    {"id":2,"name":"Gadget","price":12.99}
]

@app.route("/products", methods=["GET"])
def list_products():
    return jsonify(PRODUCTS), 20

@app.route("/products", methods=["POST"])
def add_product():
    p = request.json
    if not p or "name" not in p or "price" not in p:
        return jsonify({"error":"invalid"}), 400
    p["id"] = len(PRODUCTS) + 1
    PRODUCTS.append(p)
    return jsonify(p), 201

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002)