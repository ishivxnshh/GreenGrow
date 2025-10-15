from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from datetime import datetime, timedelta
from pymongo import MongoClient
from bson import ObjectId
import os
from dotenv import load_dotenv
import numpy as np
import pickle
import traceback
import warnings

# Suppress scikit-learn version warnings
warnings.filterwarnings("ignore", category=UserWarning, module="sklearn")

# Load environment variables
load_dotenv()

# Create Flask app as a pure API server (no static files needed)
app = Flask(__name__, static_folder=None)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-string-change-in-production')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

# Initialize extensions
jwt = JWTManager(app)
bcrypt = Bcrypt(app)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

# MongoDB connection
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/')
MONGO_DB_NAME = os.environ.get('MONGO_DB_NAME', 'greengrow')

try:
    client = MongoClient(MONGO_URI)
    db = client[MONGO_DB_NAME]
    # Test connection
    client.admin.command('ping')
    print("Database connection successful")
except Exception as e:
    print(f"Database connection failed: {e}")
    db = None

# User collection
users_collection = db.users if db is not None else None

# Helper to load pickle with better error reporting
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

# Load model + scalers with explicit checks
model = load_pickle_file("model.pkl")
mx = load_pickle_file("minmaxscaler.pkl")
sc = load_pickle_file("standscaler.pkl")

# Mapping dicts
crop_dict = {
    'rice': 1, 'maize': 2, 'chickpea': 3, 'kidneybeans': 4, 'pigeonpeas': 5,
    'mothbeans': 6, 'mungbean': 7, 'blackgram': 8, 'lentil': 9, 'pomegranate': 10,
    'banana': 11, 'mango': 12, 'grapes': 13, 'watermelon': 14, 'muskmelon': 15,
    'apple': 16, 'orange': 17, 'papaya': 18, 'coconut': 19, 'cotton': 20,
    'jute': 21, 'coffee': 22
}
inv_crop_dict = {v: k for k, v in crop_dict.items()}

# Tips
tips = {
    "rice": "🌾 Needs heavy rainfall & humid conditions.",
    "maize": "🌽 Grows well in warm climate with moderate rainfall.",
    "chickpea": "🥘 Requires dry climate, avoid excess water.",
    "kidneybeans": "🍛 Prefers moderate rainfall & loamy soil.",
    "pigeonpeas": "🌱 Needs long warm season with low humidity.",
    "mothbeans": "🌿 Grows best in arid and semi-arid regions.",
    "mungbean": "🥗 Short duration crop, prefers warm humid climate.",
    "blackgram": "⚫ Needs warm weather with moderate rains.",
    "lentil": "🥬 Prefers cool climate, well-drained soil.",
    "pomegranate": "🍎 Grows in hot dry climate with low water.",
    "banana": "🍌 High humidity, requires rich loamy soil.",
    "mango": "🥭 Needs tropical climate with hot summers.",
    "grapes": "🍇 Requires dry warm summers, deep soil.",
    "watermelon": "🍉 Hot climate with sandy soil works best.",
    "muskmelon": "🍈 Grows in warm and dry climate.",
    "apple": "🍏 Requires cold climate, hilly areas.",
    "orange": "🍊 Subtropical climate, requires well-drained soil.",
    "papaya": "🥭 Needs tropical climate with good rainfall.",
    "coconut": "🥥 Hot & humid coastal regions best.",
    "cotton": "👕 Black soil & warm climate with low humidity.",
    "jute": "🧵 Requires warm humid climate & alluvial soil.",
    "coffee": "☕ Prefers cool shade & well-drained soil."
}

@app.before_request
def log_request_info():
    # Simplified logging to prevent issues
    print(f"Request: {request.method} {request.path}")

# Authentication Routes
@app.route("/api/auth/register", methods=["POST"])
def register():
    try:
        if users_collection is None:
            return jsonify({"error": "Database connection not available"}), 500
            
        data = request.get_json()
        
        # Validate required fields
        if not data or not data.get('username') or not data.get('email') or not data.get('password'):
            return jsonify({"error": "Username, email, and password are required"}), 400
        
        username = data['username'].strip()
        email = data['email'].strip().lower()
        password = data['password']
        
        # Validate input
        if len(username) < 3:
            return jsonify({"error": "Username must be at least 3 characters long"}), 400
        
        if len(password) < 6:
            return jsonify({"error": "Password must be at least 6 characters long"}), 400
        
        if '@' not in email:
            return jsonify({"error": "Invalid email format"}), 400
        
        # Check if user already exists
        if users_collection.find_one({"username": username}):
            return jsonify({"error": "Username already exists"}), 400
        
        if users_collection.find_one({"email": email}):
            return jsonify({"error": "Email already registered"}), 400
        
        # Create new user
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
        
        # Create access token
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
        
        if not data or not data.get('username') or not data.get('password'):
            return jsonify({"error": "Username and password are required"}), 400
        
        username = data['username'].strip()
        password = data['password']
        
        # Find user by username or email
        user = users_collection.find_one({
            "$or": [
                {"username": username},
                {"email": username}
            ]
        })
        
        if not user or not bcrypt.check_password_hash(user['password_hash'], password):
            return jsonify({"error": "Invalid credentials"}), 401
        
        if not user.get('is_active', True):
            return jsonify({"error": "Account is deactivated"}), 401
        
        # Create access token
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
    # In a more sophisticated setup, you might want to blacklist the token
    # For now, we'll just return a success message
    return jsonify({"message": "Logged out successfully"}), 200

# Protected Crop Prediction Route
@app.route("/api/predict", methods=["POST"])
@jwt_required()
def api_predict():
    try:
        if not model or not mx or not sc:
            return jsonify({"error": "❌ Model or scaler files not loaded. Check server logs for missing files."}), 500

        data = request.get_json()
        print("Received data:", data)  # Log incoming data

        N = float(data.get("N", 0))
        P = float(data.get("P", 0))
        K = float(data.get("K", 0))
        temperature = float(data.get("temperature", 0))
        humidity = float(data.get("humidity", 0))
        ph = float(data.get("ph", 0))
        rainfall = float(data.get("rainfall", 0))

        # Improved validation: collect all errors
        errors = []
        if N < 0 or P < 0 or K < 0:
            errors.append("❌ N, P, K cannot be negative.")
        if N < 5 and P < 5 and K < 5:
            errors.append("❌ Soil nutrients (N, P, K) too low for any crop.")
        if rainfall < 20 or rainfall > 400:
            errors.append("❌ Rainfall not suitable (20–400 mm).")
        if not (10 <= temperature <= 45):
            errors.append("❌ Temperature not suitable (10–45°C).")
        if not (20 <= humidity <= 95):
            errors.append("❌ Humidity not suitable (20–95%).")
        if not (4.5 <= ph <= 9.0):
            errors.append("❌ Soil pH not suitable (4.5–9.0).")

        if errors:
            return jsonify({"error": errors}), 400

        # ✅ Prediction
        features = np.array([[N, P, K, temperature, humidity, ph, rainfall]])
        features = mx.transform(features)
        features = sc.transform(features)

        pred = model.predict(features)[0]
        crop_name = inv_crop_dict.get(pred, "Unknown")
        tip = tips.get(crop_name, "No tip available.")

        # Get user info for logging
        user_id = get_jwt_identity()
        user = users_collection.find_one({"_id": ObjectId(user_id)}) if users_collection else None
        print(f"Prediction made by user: {user['username'] if user else 'Unknown'}")

        # ✅ Send JSON response
        return jsonify({"crop": crop_name, "tip": tip})

    except Exception as e:
        print("❌ Exception in /api/predict:", e)
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/", methods=["GET"])
def health_check():
    return jsonify({"status": "ok", "message": "GreenGrow API is running"}), 200

if __name__ == "__main__":
    # Disable debug mode and auto-reloader to prevent socket issues on Windows
    app.run(debug=False, host="0.0.0.0", port=5000, threaded=True)