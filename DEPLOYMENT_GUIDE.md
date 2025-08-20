# TS2JS2dotSH Converter - Local Deployment Guide

## 🚀 Quick Start

Yes! You can absolutely copy these files and run the TS2JS2dotSH converter on your own system. Here's everything you need:

## 📋 Prerequisites

### Required Software:
- **Python 3.11+** 
- **Node.js 18+** (with npm or yarn)
- **MongoDB** (local installation or cloud instance)
- **TypeScript Compiler** (`npm install -g typescript`)

### System Requirements:
- **Linux/macOS/Windows** (with WSL for Windows)
- **4GB RAM minimum** 
- **2GB free disk space**

## 📁 Project Structure

```
ts2js2dotsh/
├── backend/
│   ├── server.py          # FastAPI backend
│   ├── requirements.txt   # Python dependencies
│   └── .env              # Backend environment variables
├── frontend/
│   ├── src/
│   │   ├── App.js        # React main component
│   │   ├── App.css       # Styles
│   │   └── index.js      # Entry point
│   ├── package.json      # Node.js dependencies
│   └── .env             # Frontend environment variables
└── README.md
```

## 🛠️ Installation Steps

### 1. Copy Project Files
```bash
# Copy all files from the /app directory to your local machine
# You need: backend/, frontend/, and all configuration files
```

### 2. Set Up Backend

```bash
cd backend

# Create Python virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Update .env file for local development
echo "MONGO_URL=mongodb://localhost:27017" > .env
echo "DB_NAME=ts2js2dotsh" >> .env
echo "CORS_ORIGINS=http://localhost:3000" >> .env
```

### 3. Set Up Frontend

```bash
cd frontend

# Install Node.js dependencies
yarn install
# or: npm install

# Update .env file for local development
echo "REACT_APP_BACKEND_URL=http://localhost:8001" > .env
echo "WDS_SOCKET_PORT=3000" >> .env
```

### 4. Install Global Dependencies

```bash
# Install TypeScript compiler globally
npm install -g typescript @types/node

# Verify installation
tsc --version
node --version
```

### 5. Set Up MongoDB

#### Option A: Local MongoDB
```bash
# Install MongoDB locally (Ubuntu/Debian)
sudo apt update
sudo apt install mongodb

# Start MongoDB service
sudo systemctl start mongodb
sudo systemctl enable mongodb
```

#### Option B: MongoDB Cloud (Atlas)
1. Create free account at https://mongodb.com/atlas
2. Create cluster and get connection string
3. Update `MONGO_URL` in backend/.env

### 6. Start the Application

#### Terminal 1 - Backend:
```bash
cd backend
source venv/bin/activate  # Activate virtual environment
python -m uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

#### Terminal 2 - Frontend:
```bash
cd frontend
yarn start
# or: npm start
```

## 🌐 Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8001
- **API Docs**: http://localhost:8001/docs

## 🔧 Configuration Files

### Backend Environment (.env)
```env
MONGO_URL=mongodb://localhost:27017
DB_NAME=ts2js2dotsh
CORS_ORIGINS=http://localhost:3000
```

### Frontend Environment (.env)
```env
REACT_APP_BACKEND_URL=http://localhost:8001
WDS_SOCKET_PORT=3000
```

## ✅ Verification

1. **Backend Health Check**:
   ```bash
   curl http://localhost:8001/api/
   # Should return: {"message":"TS2JS2dotSH Converter API","version":"1.0.0"}
   ```

2. **Frontend Loading**: 
   - Visit http://localhost:3000
   - You should see the TS2JS2dotSH interface

3. **Database Connection**:
   ```bash
   # Check if MongoDB is running
   mongo --eval "db.stats()"
   ```

## 🔄 Usage Workflow

1. **Upload Project**: 
   - Enter project name
   - Upload TypeScript files (.ts, .tsx, .js, .json)

2. **Conversion Process**:
   - Backend compiles TypeScript → JavaScript
   - Creates self-contained shell executable
   - Tracks progress in real-time

3. **Download Executable**:
   - Download the generated .sh file
   - Make it executable: `chmod +x yourproject.sh`
   - Run it: `./yourproject.sh`

## 🐛 Troubleshooting

### Common Issues:

**Backend won't start:**
```bash
# Check Python version
python --version  # Should be 3.11+

# Check if MongoDB is running
sudo systemctl status mongodb

# Check if port 8001 is available
lsof -i :8001
```

**Frontend won't start:**
```bash
# Check Node.js version
node --version  # Should be 18+

# Clear cache and reinstall
rm -rf node_modules package-lock.json
yarn install
```

**TypeScript compilation fails:**
```bash
# Install TypeScript globally
npm install -g typescript

# Verify installation
tsc --version
```

**CORS Errors:**
- Ensure backend .env has correct CORS_ORIGINS
- Restart backend after changing .env

## 🚀 Production Deployment

For production deployment:

1. **Use Production Database**: MongoDB Atlas or dedicated server
2. **Environment Variables**: Use production URLs
3. **Process Manager**: Use PM2 or similar for backend
4. **Web Server**: Use Nginx for frontend serving
5. **HTTPS**: Set up SSL certificates
6. **Monitoring**: Add logging and health checks

## 📦 Docker Deployment (Optional)

Create `docker-compose.yml`:
```yaml
version: '3.8'
services:
  mongodb:
    image: mongo:latest
    ports:
      - "27017:27017"
  
  backend:
    build: ./backend
    ports:
      - "8001:8001"
    depends_on:
      - mongodb
  
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend
```

## 🎯 Summary

**Yes, the TS2JS2dotSH converter is fully portable!** Users can:

✅ Copy all project files to their local system
✅ Follow this setup guide to install dependencies  
✅ Run both backend and frontend locally
✅ Convert TypeScript projects to shell executables
✅ Deploy to their own servers for production use

The application is completely self-contained and doesn't rely on any external services except MongoDB for job storage.