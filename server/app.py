# app.py (paste whole file, replaces your previous one)
import os
import traceback
import warnings
import numpy as np
import pickle
import requests
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required, get_jwt_identity
)
from pymongo import MongoClient
from bson import ObjectId
from dotenv import load_dotenv

# ===============================
# CONFIGURATION & INITIALIZATION
# ===============================

warnings.filterwarnings("ignore", category=UserWarning, module="sklearn")
warnings.filterwarnings("ignore", category=FutureWarning, module="sklearn")

load_dotenv()

app = Flask(__name__, static_folder=None)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "your-secret-key")
app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "jwt-secret-key")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=24)

bcrypt = Bcrypt(app)
jwt = JWTManager(app)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

# ===============================
# DATABASE CONNECTION
# ===============================

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
MONGO_DB_NAME = os.environ.get("MONGO_DB_NAME", "greengrow")

try:
    client = MongoClient(MONGO_URI)
    db = client[MONGO_DB_NAME]
    client.admin.command("ping")
    print("✅ Database connection successful")
except Exception as e:
    print(f"❌ Database connection failed: {e}")
    db = None

users_collection = db.users if db is not None else None
payments_collection = db["payments"] if db is not None else None

# ===============================
# MODEL LOADING
# ===============================

def load_pickle_file(filename):
    abs_path = os.path.abspath(filename)
    if not os.path.exists(abs_path):
        print(f"❌ File not found: {abs_path}")
        return None
    try:
        with open(abs_path, "rb") as f:
            return pickle.load(f)
    except Exception as e:
        print(f"❌ Error loading {abs_path}: {e}")
        return None

model = load_pickle_file("model.pkl")
mx = load_pickle_file("minmaxscaler.pkl")
sc = load_pickle_file("standscaler.pkl")

crop_dict = {
    'rice': 1, 'maize': 2, 'chickpea': 3, 'kidneybeans': 4, 'pigeonpeas': 5,
    'mothbeans': 6, 'mungbean': 7, 'blackgram': 8, 'lentil': 9, 'pomegranate': 10,
    'banana': 11, 'mango': 12, 'grapes': 13, 'watermelon': 14, 'muskmelon': 15,
    'apple': 16, 'orange': 17, 'papaya': 18, 'coconut': 19, 'cotton': 20,
    'jute': 21, 'coffee': 22
}
inv_crop_dict = {v: k for k, v in crop_dict.items()}

tips = {
    "rice": "🌾 Needs heavy rainfall & humid conditions.",
    # (you can keep your full `tips` map here; omitted for brevity)
}

# ===============================
# ROUTES: Auth, Predict (unchanged)
# ===============================

@app.before_request
def log_request_info():
    print(f"Request: {request.method} {request.path}")

@app.route("/api/auth/register", methods=["POST"])
def register():
    try:
        if users_collection is None:
            return jsonify({"error": "Database connection not available"}), 500
        data = request.get_json()
        if not data or not data.get('username') or not data.get('email') or not data.get('password'):
            return jsonify({"error": "Username, email, and password are required"}), 400
        username = data['username'].strip()
        email = data['email'].strip().lower()
        password = data['password']
        if len(username) < 3:
            return jsonify({"error": "Username must be at least 3 characters long"}), 400
        if len(password) < 6:
            return jsonify({"error": "Password must be at least 6 characters long"}), 400
        if '@' not in email:
            return jsonify({"error": "Invalid email format"}), 400
        if users_collection.find_one({"username": username}):
            return jsonify({"error": "Username already exists"}), 400
        if users_collection.find_one({"email": email}):
            return jsonify({"error": "Email already registered"}), 400
        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        user_data = {
            "username": username,
            "email": email,
            "password_hash": password_hash,
            "created_at": datetime.utcnow(),
            "is_active": True
        }
        result = users_collection.insert_one(user_data)
        user_id = str(result.inserted_id)
        access_token = create_access_token(identity=user_id)
        return jsonify({
            "message": "User registered successfully",
            "access_token": access_token,
            "user": {
                "id": user_id,
                "username": username,
                "email": email,
                "created_at": user_data["created_at"].isoformat(),
                "is_active": True
            }
        }), 201
    except Exception as e:
        print(f"❌ Registration error: {e}")
        traceback.print_exc()
        return jsonify({"error": "Registration failed"}), 500

@app.route("/api/auth/login", methods=["POST"])
def login():
    try:
        if users_collection is None:
            return jsonify({"error": "Database connection not available"}), 500
        data = request.get_json()
        if not data or not (data.get('username') or data.get('email')) or not data.get('password'):
            return jsonify({"error": "Username/email and password are required"}), 400

        # accept either username or email from frontend:
        identifier = data.get('username') if data.get('username') else data.get('email')
        identifier = identifier.strip().lower()
        password = data['password']

        user = users_collection.find_one({
            "$or": [
                {"username": identifier},
                {"email": identifier}
            ]
        })

        if not user or not bcrypt.check_password_hash(user['password_hash'], password):
            return jsonify({"error": "Invalid credentials"}), 401
        if not user.get('is_active', True):
            return jsonify({"error": "Account is deactivated"}), 401

        user_id = str(user['_id'])
        access_token = create_access_token(identity=user_id)

        return jsonify({
            "message": "Login successful",
            "access_token": access_token,
            "user": {
                "id": user_id,
                "username": user['username'],
                "email": user['email'],
                "created_at": user['created_at'].isoformat(),
                "is_active": user.get('is_active', True)
            }
        }), 200
    except Exception as e:
        print(f"❌ Login error: {e}")
        traceback.print_exc()
        return jsonify({"error": "Login failed"}), 500

@app.route("/api/auth/profile", methods=["GET"])
@jwt_required()
def get_profile():
    try:
        if users_collection is None:
            return jsonify({"error": "Database connection not available"}), 500
        user_id = get_jwt_identity()
        user = users_collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            return jsonify({"error": "User not found"}), 404
        return jsonify({
            "user": {
                "id": str(user['_id']),
                "username": user['username'],
                "email": user['email'],
                "created_at": user['created_at'].isoformat(),
                "is_active": user.get('is_active', True)
            }
        }), 200
    except Exception as e:
        print(f"❌ Profile error: {e}")
        return jsonify({"error": "Failed to get profile"}), 500

@app.route("/api/auth/logout", methods=["POST"])
@jwt_required()
def logout():
    return jsonify({"message": "Logged out successfully"}), 200

@app.route("/api/predict", methods=["POST"])
@jwt_required()
def api_predict():
    try:
        if not model or not mx or not sc:
            return jsonify({"error": "❌ Model or scaler files not loaded. Check server logs for missing files."}), 500
        data = request.get_json()
        print("Received data:", data)
        N = float(data.get("N", 0))
        P = float(data.get("P", 0))
        K = float(data.get("K", 0))
        temperature = float(data.get("temperature", 0))
        humidity = float(data.get("humidity", 0))
        ph = float(data.get("ph", 0))
        rainfall = float(data.get("rainfall", 0))

        errors = []
        if N < 0 or P < 0 or K < 0:
            errors.append("❌ N, P, K cannot be negative.")
        if N < 5 and P < 5 and K < 5:
            errors.append("❌ Soil nutrients (N, P, K) too low for any crop.")
        if rainfall < 20 or rainfall > 400:
            errors.append("❌ Rainfall not suitable (20–400 mm).")
        if not (10 <= temperature <= 45):
            errors.append("❌ Temperature not suitable (10–45°C).")
        if not (14 <= humidity <= 95):
            errors.append("❌ Humidity not suitable (14–95%).")
        if not (4.5 <= ph <= 9.0):
            errors.append("❌ Soil pH not suitable (4.5–9.0).")
        if errors:
            return jsonify({"error": errors}), 400

        features = np.array([[N, P, K, temperature, humidity, ph, rainfall]])
        features = mx.transform(features)
        features = sc.transform(features)

        pred = model.predict(features)[0]
        crop_name = inv_crop_dict.get(pred, "Unknown")
        tip = tips.get(crop_name, "No tip available.")
        user_id = get_jwt_identity()
        user = users_collection.find_one({"_id": ObjectId(user_id)}) if users_collection is not None else None
        print(f"Prediction made by user: {user['username'] if user else 'Unknown'}")
        return jsonify({"crop": crop_name, "tip": tip})
    except Exception as e:
        print("❌ Exception in /api/predict:", e)
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/", methods=["GET"])
def health_check():
    return jsonify({"status": "ok", "message": "GreenGrow API is running"}), 200

# ===============================
# PAYMENTS: record & status (client-side captured PayPal)
# ===============================

@app.route("/api/payment/success", methods=["POST"])
@jwt_required()
def record_payment():
    """
    Frontend calls this AFTER PayPal capture (client captures using PayPal SDK),
    sending order details so we can store it and unlock the feature.
    """
    try:
        if payments_collection is None:
            return jsonify({"error": "Database connection not available"}), 500

        user_id = get_jwt_identity()
        data = request.get_json()
        payment_id = data.get("payment_id") or data.get("id")  # accept either shape
        amount = data.get("amount")
        currency = data.get("currency", "USD")

        if not payment_id or not amount:
            return jsonify({"error": "Invalid payment data"}), 400

        existing = payments_collection.find_one({"user_id": ObjectId(user_id), "payment_id": payment_id})
        if existing:
            return jsonify({"message": "Payment already recorded"}), 200

        payment_doc = {
            "user_id": ObjectId(user_id),
            "payment_id": payment_id,
            "amount": float(amount),
            "currency": currency,
            "status": "completed",
            "service": "disease_detection",
            "created_at": datetime.utcnow()
        }
        payments_collection.insert_one(payment_doc)
        print(f"✅ Payment recorded for user {user_id}: {payment_id}")
        return jsonify({"message": "Payment recorded", "payment_id": payment_id}), 201

    except Exception as e:
        print(f"❌ Payment recording error: {e}")
        traceback.print_exc()
        return jsonify({"error": "Failed to record payment"}), 500

@app.route("/api/payment/status", methods=["GET"])
@jwt_required()
def payment_status():
    try:
        if payments_collection is None:
            return jsonify({"error": "Database connection not available"}), 500
        user_id = get_jwt_identity()
        payment = payments_collection.find_one({"user_id": ObjectId(user_id), "status": "completed"})
        has_paid = payment is not None
        return jsonify({
            "hasPaid": has_paid,
            "payment_details": {
                "amount": payment.get("amount") if payment else None,
                "date": payment.get("created_at").isoformat() if payment else None
            } if payment else None
        }), 200
    except Exception as e:
        print(f"❌ Payment status check error: {e}")
        traceback.print_exc()
        return jsonify({"error": "Failed to check payment status"}), 500

# ===============================
# MAIN ENTRY
# ===============================

if __name__ == "__main__":
    print("🚀 Flask running at http://localhost:5000")
    app.run(debug=False, host="0.0.0.0", port=5000, threaded=True)
