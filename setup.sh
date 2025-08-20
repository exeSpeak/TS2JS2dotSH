#!/bin/bash

# TS2JS2dotSH Converter - Automated Setup Script
# This script sets up the TS2JS2dotSH converter on a local system

set -e  # Exit on any error

echo "🚀 TS2JS2dotSH Converter - Local Setup"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}$1${NC}"
}

# Check if script is run from project root
if [ ! -f "backend/server.py" ] || [ ! -f "frontend/package.json" ]; then
    print_error "Please run this script from the project root directory"
    print_error "Make sure you have both backend/ and frontend/ directories"
    exit 1
fi

print_header "📋 Checking Prerequisites..."

# Check Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    print_status "Python found: $PYTHON_VERSION"
else
    print_error "Python 3 is not installed. Please install Python 3.11 or higher."
    exit 1
fi

# Check Node.js
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    print_status "Node.js found: $NODE_VERSION"
else
    print_error "Node.js is not installed. Please install Node.js 18 or higher."
    exit 1
fi

# Check package manager
if command -v yarn &> /dev/null; then
    PACKAGE_MANAGER="yarn"
    print_status "Using Yarn package manager"
elif command -v npm &> /dev/null; then
    PACKAGE_MANAGER="npm"
    print_status "Using NPM package manager"
else
    print_error "Neither yarn nor npm found. Please install Node.js with npm."
    exit 1
fi

# Check MongoDB
if command -v mongod &> /dev/null; then
    print_status "MongoDB found"
    MONGO_LOCAL=true
else
    print_warning "MongoDB not found locally"
    print_warning "You'll need to set up MongoDB manually or use MongoDB Atlas"
    MONGO_LOCAL=false
fi

print_header "🔧 Installing Global Dependencies..."

# Install TypeScript globally
if command -v tsc &> /dev/null; then
    TSC_VERSION=$(tsc --version)
    print_status "TypeScript already installed: $TSC_VERSION"
else
    print_status "Installing TypeScript globally..."
    npm install -g typescript @types/node
fi

print_header "🏗️  Setting up Backend..."

cd backend

# Create virtual environment
if [ ! -d "venv" ]; then
    print_status "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate

# Install Python dependencies
print_status "Installing Python dependencies..."
pip install -r requirements.txt

# Create backend .env file
print_status "Creating backend environment file..."
cat > .env << EOF
MONGO_URL=mongodb://localhost:27017
DB_NAME=ts2js2dotsh
CORS_ORIGINS=http://localhost:3000
EOF

cd ..

print_header "🎨 Setting up Frontend..."

cd frontend

# Install Node.js dependencies
print_status "Installing Node.js dependencies..."
if [ "$PACKAGE_MANAGER" = "yarn" ]; then
    yarn install
else
    npm install
fi

# Create frontend .env file
print_status "Creating frontend environment file..."
cat > .env << EOF
REACT_APP_BACKEND_URL=http://localhost:8001
WDS_SOCKET_PORT=3000
EOF

cd ..

print_header "📝 Creating Start Scripts..."

# Create backend start script
cat > start-backend.sh << 'EOF'
#!/bin/bash
cd backend
source venv/bin/activate
echo "🚀 Starting TS2JS2dotSH Backend on http://localhost:8001"
python -m uvicorn server:app --host 0.0.0.0 --port 8001 --reload
EOF

chmod +x start-backend.sh

# Create frontend start script
cat > start-frontend.sh << 'EOF'
#!/bin/bash
cd frontend
echo "🎨 Starting TS2JS2dotSH Frontend on http://localhost:3000"
if command -v yarn &> /dev/null; then
    yarn start
else
    npm start
fi
EOF

chmod +x start-frontend.sh

# Create combined start script
cat > start-all.sh << 'EOF'
#!/bin/bash
echo "🚀 Starting TS2JS2dotSH Converter..."
echo "Backend: http://localhost:8001"
echo "Frontend: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop all services"

# Function to cleanup background processes
cleanup() {
    echo "Stopping services..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    wait $BACKEND_PID $FRONTEND_PID 2>/dev/null
    echo "Services stopped."
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start backend in background
./start-backend.sh &
BACKEND_PID=$!

# Wait a bit for backend to start
sleep 5

# Start frontend in background
./start-frontend.sh &
FRONTEND_PID=$!

# Wait for processes
wait $BACKEND_PID $FRONTEND_PID
EOF

chmod +x start-all.sh

print_header "✅ Setup Complete!"

echo ""
print_status "Setup completed successfully! 🎉"
echo ""
print_header "📋 Next Steps:"
echo ""
echo "1. Start MongoDB (if using local MongoDB):"
if [ "$MONGO_LOCAL" = true ]; then
    echo "   sudo systemctl start mongodb"
    echo "   # or: brew services start mongodb/brew/mongodb-community (macOS)"
else
    echo "   Set up MongoDB Atlas: https://mongodb.com/atlas"
    echo "   Update backend/.env with your MongoDB connection string"
fi
echo ""
echo "2. Start the application:"
echo "   ./start-all.sh           # Start both backend and frontend"
echo "   # OR start them separately:"
echo "   ./start-backend.sh       # Start backend only"
echo "   ./start-frontend.sh      # Start frontend only"
echo ""
echo "3. Access the application:"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:8001"
echo "   API Docs: http://localhost:8001/docs"
echo ""
print_header "🔍 Test the setup:"
echo "   curl http://localhost:8001/api/"
echo ""
print_status "Happy TypeScript converting! 🚀"