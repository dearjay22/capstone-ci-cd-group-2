from flask import Flask, render_template, request
import requests, os

app = Flask(__name__, template_folder="templates")

USERS_HOST = os.environ.get("USERS_HOST", "http://localhost:5001")
PRODUCTS_HOST = os.environ.get("PRODUCTS_HOST", "http://localhost:5002")
ORDERS_HOST = os.environ.get("ORDERS_HOST", "http://localhost:5003")

@app.route("/")
def index():
    try:
        users = requests.get(f"{USERS_HOST}/users").json()
    except Exception:
        users = []
    try:
        products = requests.get(f"{PRODUCTS_HOST}/products").json()
    except Exception:
        products = []
    return render_template("index.html", users=users, products=products)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)