# GreenGrow - Smart Agriculture Platform

An integrated platform for smart agriculture solutions including crop recommendations, disease detection, and soil restoration.

## Project Structure

```
GreenGrow/
├── client/          # Frontend React application
│   ├── src/         # React source code
│   ├── public/      # Static assets
│   └── package.json # Frontend dependencies
├── server/          # Backend API services
│   ├── app.py       # Flask API server
│   └── ...          # ML models and data files
└── README.md        # This file
```

## Getting Started

### Frontend (Client)
```bash
cd client
npm install
npm run dev
```

### Backend (Server)
```bash
cd server
pip install -r requirements.txt
# Make sure MongoDB is running
python app.py
```

## Features

- 🔐 **User Authentication** - Secure login and registration system
- 🌱 **Smart Crop Recommendations** - AI-powered crop suggestions based on soil and climate data
- 🔍 **Disease Detection** - Identify plant diseases early
- 🌿 **Soil Restoration Guidance** - Improve soil health and fertility
- 📊 **Data-driven Agriculture Insights** - Personalized recommendations for farmers
- 🛡️ **Protected Routes** - Secure access to premium features

## Authentication

The application includes a complete authentication system:

- **Registration**: Users can create accounts with username, email, and password
- **Login**: Secure authentication with JWT tokens
- **Protected Routes**: Crop recommendations and other premium features require authentication
- **Session Management**: Automatic token refresh and logout functionality