from fastapi import FastAPI, APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Form
from fastapi.responses import FileResponse, StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import aiofiles
import shutil
import subprocess
import tempfile
import zipfile
import json
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
import asyncio

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(
    title="TS2JS2dotSH Converter",
    description="Convert TypeScript projects to executable shell scripts",
    version="1.0.0"
)

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Create uploads directory
UPLOAD_DIR = Path("/tmp/ts2sh_uploads")
OUTPUT_DIR = Path("/tmp/ts2sh_outputs")
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# Define Models
class ConversionJob(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_name: str
    status: str = "pending"  # pending, processing, completed, failed
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    error_message: Optional[str] = None
    output_file: Optional[str] = None

class ConversionRequest(BaseModel):
    project_name: str

class ConversionResponse(BaseModel):
    job_id: str
    status: str
    message: str

class ConversionStatus(BaseModel):
    job_id: str
    status: str
    progress: int
    message: str
    download_url: Optional[str] = None
    error_message: Optional[str] = None

# TypeScript to JavaScript compilation function
async def compile_typescript_project(project_path: Path, output_path: Path) -> Dict[str, Any]:
    """Compile TypeScript project to JavaScript."""
    try:
        # Check if package.json exists
        package_json_path = project_path / "package.json"
        tsconfig_path = project_path / "tsconfig.json"
        
        # Create default tsconfig.json if it doesn't exist
        if not tsconfig_path.exists():
            default_tsconfig = {
                "compilerOptions": {
                    "target": "ES2020",
                    "module": "commonjs",
                    "outDir": str(output_path / "compiled"),
                    "rootDir": str(project_path),
                    "strict": True,
                    "esModuleInterop": True,
                    "skipLibCheck": True,
                    "forceConsistentCasingInFileNames": True,
                    "resolveJsonModule": True
                },
                "exclude": ["node_modules", "**/*.test.ts", "**/*.spec.ts"]
            }
            
            async with aiofiles.open(tsconfig_path, 'w') as f:
                await f.write(json.dumps(default_tsconfig, indent=2))
        
        # Install dependencies if package.json exists
        if package_json_path.exists():
            install_process = await asyncio.create_subprocess_exec(
                'npm', 'install',
                cwd=project_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await install_process.communicate()
        
        # Compile TypeScript
        compile_process = await asyncio.create_subprocess_exec(
            'tsc', '--project', str(tsconfig_path),
            cwd=project_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await compile_process.communicate()
        
        if compile_process.returncode != 0:
            return {
                "success": False,
                "error": f"TypeScript compilation failed: {stderr.decode()}"
            }
        
        return {
            "success": True,
            "message": "TypeScript compilation successful",
            "compiled_dir": output_path / "compiled"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Compilation error: {str(e)}"
        }

async def create_shell_executable(compiled_dir: Path, output_file: Path, project_name: str) -> Dict[str, Any]:
    """Create a self-contained shell executable from compiled JavaScript."""
    try:
        # Find the main entry point
        main_files = ["index.js", "main.js", "app.js"]
        entry_point = None
        
        for main_file in main_files:
            if (compiled_dir / main_file).exists():
                entry_point = main_file
                break
        
        # If no standard entry point found, use the first .js file
        if not entry_point:
            js_files = list(compiled_dir.glob("*.js"))
            if js_files:
                entry_point = js_files[0].name
            else:
                return {
                    "success": False,
                    "error": "No JavaScript files found in compiled output"
                }
        
        # Create the shell script
        shell_script_content = f'''#!/bin/bash

# TS2JS2dotSH Generated Executable
# Project: {project_name}
# Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "Error: Node.js is not installed. Please install Node.js to run this executable."
    exit 1
fi

# Create temporary directory for execution
TEMP_DIR=$(mktemp -d)
cd "$TEMP_DIR"

# Extract embedded files
extract_files() {{
    # This function will contain the embedded JavaScript files
    cat << 'EOF_MAIN_JS' > {entry_point}
'''
        
        # Read and embed the main JavaScript file
        main_js_path = compiled_dir / entry_point
        async with aiofiles.open(main_js_path, 'r') as f:
            main_js_content = await f.read()
        
        shell_script_content += main_js_content
        shell_script_content += '''
EOF_MAIN_JS

'''
        
        # Embed other JavaScript files
        for js_file in compiled_dir.glob("*.js"):
            if js_file.name != entry_point:
                async with aiofiles.open(js_file, 'r') as f:
                    js_content = await f.read()
                
                shell_script_content += f'''    cat << 'EOF_{js_file.name.upper().replace(".", "_")}' > {js_file.name}
{js_content}
EOF_{js_file.name.upper().replace(".", "_")}

'''
        
        # Add package.json if it exists in the original project
        original_package_json = compiled_dir.parent / "package.json"
        if original_package_json.exists():
            async with aiofiles.open(original_package_json, 'r') as f:
                package_content = await f.read()
            
            shell_script_content += f'''    cat << 'EOF_PACKAGE_JSON' > package.json
{package_content}
EOF_PACKAGE_JSON

    # Install dependencies if package.json exists
    if [ -f "package.json" ]; then
        echo "Installing dependencies..."
        npm install --silent > /dev/null 2>&1
    fi
'''
        
        # Complete the shell script
        shell_script_content += f'''}}

# Cleanup function
cleanup() {{
    cd /
    rm -rf "$TEMP_DIR"
}}

# Set trap to cleanup on exit
trap cleanup EXIT

# Extract files and run
extract_files

echo "Running {project_name}..."
echo "----------------------------------------"

# Execute the main JavaScript file
node {entry_point} "$@"

# Keep the cleanup trap
'''
        
        # Write the shell script
        async with aiofiles.open(output_file, 'w') as f:
            await f.write(shell_script_content)
        
        # Make it executable
        os.chmod(output_file, 0o755)
        
        return {
            "success": True,
            "message": f"Shell executable created successfully: {output_file.name}",
            "executable_path": str(output_file)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Shell script creation error: {str(e)}"
        }

async def process_conversion_job(job_id: str, project_path: Path, project_name: str):
    """Background task to process TypeScript conversion."""
    try:
        # Update job status to processing
        await db.conversion_jobs.update_one(
            {"id": job_id},
            {"$set": {"status": "processing", "updated_at": datetime.utcnow()}}
        )
        
        # Create output directory for this job
        job_output_dir = OUTPUT_DIR / job_id
        job_output_dir.mkdir(exist_ok=True)
        
        # Step 1: Compile TypeScript to JavaScript
        compilation_result = await compile_typescript_project(project_path, job_output_dir)
        
        if not compilation_result["success"]:
            await db.conversion_jobs.update_one(
                {"id": job_id},
                {"$set": {
                    "status": "failed",
                    "error_message": compilation_result["error"],
                    "updated_at": datetime.utcnow()
                }}
            )
            return
        
        # Step 2: Create shell executable
        compiled_dir = compilation_result["compiled_dir"]
        output_file = job_output_dir / f"{project_name}.sh"
        
        shell_result = await create_shell_executable(compiled_dir, output_file, project_name)
        
        if not shell_result["success"]:
            await db.conversion_jobs.update_one(
                {"id": job_id},
                {"$set": {
                    "status": "failed",
                    "error_message": shell_result["error"],
                    "updated_at": datetime.utcnow()
                }}
            )
            return
        
        # Update job status to completed
        await db.conversion_jobs.update_one(
            {"id": job_id},
            {"$set": {
                "status": "completed",
                "output_file": f"{project_name}.sh",
                "updated_at": datetime.utcnow()
            }}
        )
        
    except Exception as e:
        await db.conversion_jobs.update_one(
            {"id": job_id},
            {"$set": {
                "status": "failed",
                "error_message": str(e),
                "updated_at": datetime.utcnow()
            }}
        )
    finally:
        # Cleanup uploaded files
        if project_path.exists():
            shutil.rmtree(project_path, ignore_errors=True)

# API Routes
@api_router.get("/")
async def root():
    return {"message": "TS2JS2dotSH Converter API", "version": "1.0.0"}

@api_router.post("/convert", response_model=ConversionResponse)
async def convert_typescript_project(
    background_tasks: BackgroundTasks,
    project_name: str = Form(...),
    files: List[UploadFile] = File(...)
):
    """Upload TypeScript project and start conversion process."""
    try:
        # Create job
        job_id = str(uuid.uuid4())
        job = ConversionJob(
            id=job_id,
            project_name=project_name,
            status="pending"
        )
        
        # Save job to database
        await db.conversion_jobs.insert_one(job.dict())
        
        # Create project directory
        project_path = UPLOAD_DIR / job_id
        project_path.mkdir(exist_ok=True)
        
        # Save uploaded files
        for file in files:
            file_path = project_path / file.filename
            
            # Create subdirectories if needed
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            async with aiofiles.open(file_path, 'wb') as f:
                content = await file.read()
                await f.write(content)
        
        # Start background processing
        background_tasks.add_task(
            process_conversion_job,
            job_id,
            project_path,
            project_name
        )
        
        return ConversionResponse(
            job_id=job_id,
            status="pending",
            message="Conversion job started successfully"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start conversion: {str(e)}")

@api_router.get("/status/{job_id}", response_model=ConversionStatus)
async def get_conversion_status(job_id: str):
    """Get the status of a conversion job."""
    try:
        job = await db.conversion_jobs.find_one({"id": job_id})
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        progress_map = {
            "pending": 10,
            "processing": 50,
            "completed": 100,
            "failed": 0
        }
        
        download_url = None
        if job["status"] == "completed" and job.get("output_file"):
            download_url = f"/api/download/{job_id}"
        
        return ConversionStatus(
            job_id=job_id,
            status=job["status"],
            progress=progress_map.get(job["status"], 0),
            message=f"Job is {job['status']}",
            download_url=download_url,
            error_message=job.get("error_message")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get job status: {str(e)}")

@api_router.get("/download/{job_id}")
async def download_executable(job_id: str):
    """Download the generated shell executable."""
    try:
        job = await db.conversion_jobs.find_one({"id": job_id})
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        if job["status"] != "completed":
            raise HTTPException(status_code=400, detail="Job not completed yet")
        
        output_file_path = OUTPUT_DIR / job_id / job["output_file"]
        
        if not output_file_path.exists():
            raise HTTPException(status_code=404, detail="Output file not found")
        
        return FileResponse(
            path=str(output_file_path),
            filename=job["output_file"],
            media_type="application/octet-stream"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to download file: {str(e)}")

@api_router.get("/jobs", response_model=List[ConversionJob])
async def get_all_jobs():
    """Get all conversion jobs."""
    try:
        jobs = await db.conversion_jobs.find().sort("created_at", -1).to_list(100)
        return [ConversionJob(**job) for job in jobs]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get jobs: {str(e)}")

@api_router.delete("/jobs/{job_id}")
async def delete_job(job_id: str):
    """Delete a conversion job and its files."""
    try:
        job = await db.conversion_jobs.find_one({"id": job_id})
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Delete files
        job_output_dir = OUTPUT_DIR / job_id
        if job_output_dir.exists():
            shutil.rmtree(job_output_dir, ignore_errors=True)
        
        # Delete from database
        await db.conversion_jobs.delete_one({"id": job_id})
        
        return {"message": "Job deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete job: {str(e)}")

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()