# TS2JS2dotSH Converter 🚀

Convert TypeScript projects into executable Linux shell scripts with a beautiful web interface.

## 🎯 What This Does

The **TS2JS2dotSH Converter** solves a real problem for the AI "vibe code" community: 

- **Input**: TypeScript projects from AI code generators
- **Output**: Self-contained executable `.sh` files that run on any Linux system
- **Result**: Clickable programs that don't require complex setup

## ✨ Features

- 🌐 **Web-based Interface**: Beautiful, intuitive upload and conversion interface
- 📁 **Multi-file Support**: Upload entire TypeScript projects at once
- ⚡ **Real-time Processing**: Live status updates and progress tracking
- 📦 **Self-contained Executables**: Generated `.sh` files include all dependencies
- 🔄 **Job Management**: Track conversion history and re-download files
- 🎨 **Professional Design**: Modern UI with drag & drop functionality

## 🚀 Quick Start

### Option 1: Run Locally (Recommended)

1. **Clone/Download** this project to your local machine
2. **Run the setup script**:
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```
3. **Start the application**:
   ```bash
   ./start-all.sh
   ```
4. **Open** http://localhost:3000 in your browser

### Option 2: Manual Setup

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed installation instructions.

## 📋 Requirements

- **Python 3.11+**
- **Node.js 18+** 
- **MongoDB** (local or cloud)
- **TypeScript** (`npm install -g typescript`)

## 🔧 How It Works

1. **Upload**: Drag & drop your TypeScript files (.ts, .tsx, .js, .json)
2. **Convert**: Backend compiles TypeScript → JavaScript → Shell executable
3. **Download**: Get a self-contained `.sh` file
4. **Execute**: Run anywhere with `./your-project.sh`

### Generated Executable Features:
- ✅ **Node.js detection**: Checks if Node.js is installed
- ✅ **Self-contained**: All code embedded in the shell script
- ✅ **Dependency handling**: Automatically installs npm packages
- ✅ **Clean execution**: Uses temporary directories
- ✅ **Automatic cleanup**: Removes temp files after execution

## 📁 Project Structure

```
ts2js2dotsh/
├── backend/
│   ├── server.py          # FastAPI backend with TS compilation
│   ├── requirements.txt   # Python dependencies
│   └── .env              # Environment configuration
├── frontend/
│   ├── src/
│   │   ├── App.js        # React main interface
│   │   └── App.css       # Modern styling
│   ├── package.json      # Node.js dependencies
│   └── .env             # Frontend configuration
├── setup.sh              # Automated setup script
├── start-all.sh          # Start both services
└── DEPLOYMENT_GUIDE.md   # Detailed setup instructions
```

## 🌐 API Endpoints

- `POST /api/convert` - Upload and convert TypeScript project
- `GET /api/status/{job_id}` - Check conversion status
- `GET /api/download/{job_id}` - Download executable
- `GET /api/jobs` - List all conversion jobs
- `DELETE /api/jobs/{job_id}` - Delete a job

## 🎨 Screenshots

The interface features:
- Modern gradient design with glass morphism effects
- Drag & drop file upload with visual feedback
- Real-time progress tracking with animated progress bars
- Job history management with download/delete actions
- Responsive design that works on all devices

## 🔧 Example Usage

```bash
# 1. Upload TypeScript files through web interface
# 2. Download the generated executable
# 3. Make it executable and run:

chmod +x my-typescript-app.sh
./my-typescript-app.sh

# The executable will:
# - Check for Node.js
# - Extract embedded JavaScript files
# - Install dependencies if needed  
# - Run your TypeScript application
# - Clean up temporary files
```

## 🐛 Troubleshooting

### Backend Issues:
```bash
# Check if backend is running
curl http://localhost:8001/api/

# Check MongoDB connection
mongo --eval "db.stats()"

# View backend logs
cd backend && source venv/bin/activate && python -m uvicorn server:app --reload
```

### Frontend Issues:
```bash
# Check if frontend is accessible
curl http://localhost:3000

# Reinstall dependencies
cd frontend && rm -rf node_modules && yarn install
```

## 🚀 Production Deployment

For production use:

1. **Database**: Use MongoDB Atlas or dedicated MongoDB server
2. **Environment**: Update `.env` files with production URLs
3. **Process Management**: Use PM2 or systemd for service management
4. **Web Server**: Use Nginx for reverse proxy and static file serving
5. **Security**: Enable HTTPS and proper CORS configuration

## 🤝 Contributing

This is a complete, working solution for converting TypeScript to shell executables. Feel free to:

- Add support for more file types
- Improve the UI/UX design
- Add more compilation options
- Enhance error handling
- Add unit tests

## 📄 License

MIT License - Feel free to use this in your own projects!

## 🎯 Perfect For

- **AI Code Generators**: Convert generated TypeScript to executables
- **Rapid Prototyping**: Quickly package TS projects for distribution
- **Educational Projects**: Share TypeScript programs as simple executables
- **DevOps**: Create deployable scripts from TypeScript utilities
- **Open Source**: Package TypeScript tools as standalone executables

---

**Built with ❤️ for the developer community**

Transform your TypeScript projects into clickable Linux programs in seconds!
