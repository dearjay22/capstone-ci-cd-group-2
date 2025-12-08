from flask import Flask, render_template, request, jsonify
import requests
import os

app = Flask(__name__, template_folder="templates")

USERS_HOST = os.environ.get("USERS_HOST", "http://localhost:5001")
PRODUCTS_HOST = os.environ.get("PRODUCTS_HOST", "http://localhost:5002")
ORDERS_HOST = os.environ.get("ORDERS_HOST", "http://localhost:5003")

@app.route("/")
def index():
    """Main page - serves the HTML interface"""
    return render_template("index.html")

@app.route("/users", methods=["GET", "POST"])
def users_proxy():
    """Proxy requests to users service"""
    try:
        if request.method == "GET":
            response = requests.get(f"{USERS_HOST}/users")
        else:
            response = requests.post(f"{USERS_HOST}/users", json=request.json)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/products", methods=["GET", "POST"])
def products_proxy():
    """Proxy requests to products service"""
    try:
        if request.method == "GET":
            response = requests.get(f"{PRODUCTS_HOST}/products")
        else:
            response = requests.post(f"{PRODUCTS_HOST}/products", json=request.json)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/orders", methods=["GET", "POST"])
def orders_proxy():
    """Proxy requests to orders service"""
    try:
        if request.method == "GET":
            response = requests.get(f"{ORDERS_HOST}/orders")
        else:
            response = requests.post(f"{ORDERS_HOST}/orders", json=request.json)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/health")
def health():
    """Health check endpoint"""
    services_status = {}
    
    # Check each service
    for service_name, service_url in [
        ("users", USERS_HOST),
        ("products", PRODUCTS_HOST),
        ("orders", ORDERS_HOST)
    ]:
        try:
            response = requests.get(f"{service_url}/health", timeout=2)
            services_status[service_name] = "healthy" if response.status_code == 200 else "unhealthy"
        except:
            services_status[service_name] = "unreachable"
    
    overall_status = "healthy" if all(s == "healthy" for s in services_status.values()) else "degraded"
    
    return jsonify({
        "status": overall_status,
        "services": services_status
    }), 200 if overall_status == "healthy" else 503

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000, debug=False)