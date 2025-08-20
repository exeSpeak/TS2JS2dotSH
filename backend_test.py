#!/usr/bin/env python3

import requests
import sys
import time
import os
from pathlib import Path
from datetime import datetime

class TS2JS2dotSHAPITester:
    def __init__(self, base_url="https://ts2executable.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.current_job_id = None
        
        # Test files from /tmp/test_ts_project/
        self.test_files_dir = Path("/tmp/test_ts_project")
        
    def log(self, message, level="INFO"):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}][{level}] {message}")

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None, timeout=30):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}" if not endpoint.startswith('http') else endpoint
        headers = {}
        
        self.tests_run += 1
        self.log(f"🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                if files:
                    response = requests.post(url, data=data, files=files, headers=headers, timeout=timeout)
                else:
                    headers['Content-Type'] = 'application/json'
                    response = requests.post(url, json=data, headers=headers, timeout=timeout)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=timeout)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                self.log(f"✅ {name} - Status: {response.status_code}", "PASS")
                try:
                    return True, response.json()
                except:
                    return True, response.text
            else:
                self.log(f"❌ {name} - Expected {expected_status}, got {response.status_code}", "FAIL")
                try:
                    error_detail = response.json()
                    self.log(f"   Error details: {error_detail}", "ERROR")
                except:
                    self.log(f"   Response text: {response.text[:200]}", "ERROR")
                return False, {}

        except requests.exceptions.Timeout:
            self.log(f"❌ {name} - Request timed out after {timeout}s", "FAIL")
            return False, {}
        except Exception as e:
            self.log(f"❌ {name} - Error: {str(e)}", "FAIL")
            return False, {}

    def test_api_root(self):
        """Test API root endpoint"""
        success, response = self.run_test(
            "API Root",
            "GET",
            "",
            200
        )
        if success:
            self.log(f"   API Message: {response.get('message', 'N/A')}")
        return success

    def test_get_jobs_empty(self):
        """Test getting jobs when none exist"""
        success, response = self.run_test(
            "Get Jobs (Empty)",
            "GET",
            "jobs",
            200
        )
        if success:
            self.log(f"   Found {len(response)} existing jobs")
        return success

    def prepare_test_files(self):
        """Prepare test files for upload"""
        test_files = []
        
        # Check if test files exist
        if not self.test_files_dir.exists():
            self.log("❌ Test files directory not found at /tmp/test_ts_project/", "ERROR")
            return None
            
        # Collect TypeScript and related files
        file_patterns = ["*.ts", "*.tsx", "*.js", "*.jsx", "*.json"]
        for pattern in file_patterns:
            for file_path in self.test_files_dir.glob(pattern):
                if file_path.is_file() and file_path.name != "yarn.lock":  # Skip yarn.lock
                    try:
                        with open(file_path, 'rb') as f:
                            content = f.read()
                        test_files.append(('files', (file_path.name, content, 'text/plain')))
                        self.log(f"   Prepared file: {file_path.name} ({len(content)} bytes)")
                    except Exception as e:
                        self.log(f"   Failed to read {file_path.name}: {e}", "ERROR")
        
        if not test_files:
            self.log("❌ No test files found to upload", "ERROR")
            return None
            
        return test_files

    def test_convert_project(self):
        """Test TypeScript project conversion"""
        test_files = self.prepare_test_files()
        if not test_files:
            return False
            
        project_name = f"test_project_{int(time.time())}"
        
        success, response = self.run_test(
            "Convert TypeScript Project",
            "POST",
            "convert",
            200,
            data={'project_name': project_name},
            files=test_files,
            timeout=60
        )
        
        if success and 'job_id' in response:
            self.current_job_id = response['job_id']
            self.log(f"   Job ID: {self.current_job_id}")
            self.log(f"   Status: {response.get('status', 'N/A')}")
            return True
        return False

    def test_job_status(self):
        """Test job status checking"""
        if not self.current_job_id:
            self.log("❌ No job ID available for status check", "ERROR")
            return False
            
        success, response = self.run_test(
            "Check Job Status",
            "GET",
            f"status/{self.current_job_id}",
            200
        )
        
        if success:
            self.log(f"   Job Status: {response.get('status', 'N/A')}")
            self.log(f"   Progress: {response.get('progress', 'N/A')}%")
            if response.get('error_message'):
                self.log(f"   Error: {response['error_message']}", "ERROR")
            return True, response
        return False, {}

    def wait_for_job_completion(self, max_wait_time=120):
        """Wait for job to complete"""
        if not self.current_job_id:
            return False, {}
            
        self.log(f"⏳ Waiting for job completion (max {max_wait_time}s)...")
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            success, response = self.test_job_status()
            if not success:
                return False, {}
                
            status = response.get('status', '')
            if status == 'completed':
                self.log("✅ Job completed successfully!")
                return True, response
            elif status == 'failed':
                self.log(f"❌ Job failed: {response.get('error_message', 'Unknown error')}", "ERROR")
                return False, response
            elif status in ['pending', 'processing']:
                self.log(f"   Still {status}... waiting 5s")
                time.sleep(5)
            else:
                self.log(f"   Unknown status: {status}")
                time.sleep(5)
                
        self.log(f"❌ Job did not complete within {max_wait_time}s", "ERROR")
        return False, {}

    def test_download_executable(self):
        """Test downloading the generated executable"""
        if not self.current_job_id:
            self.log("❌ No job ID available for download", "ERROR")
            return False
            
        # First check if job is completed
        success, status_response = self.test_job_status()
        if not success or status_response.get('status') != 'completed':
            self.log("❌ Job not completed, cannot download", "ERROR")
            return False
            
        # Test download
        download_url = f"{self.api_url}/download/{self.current_job_id}"
        
        try:
            self.log("🔍 Testing Download Executable...")
            response = requests.get(download_url, timeout=30)
            
            if response.status_code == 200:
                self.tests_passed += 1
                content_length = len(response.content)
                self.log(f"✅ Download Executable - Downloaded {content_length} bytes", "PASS")
                
                # Save the file for verification
                download_path = f"/tmp/test_executable_{self.current_job_id}.sh"
                with open(download_path, 'wb') as f:
                    f.write(response.content)
                
                # Check if it's executable
                os.chmod(download_path, 0o755)
                self.log(f"   Saved executable to: {download_path}")
                
                # Verify it's a shell script
                with open(download_path, 'r') as f:
                    first_line = f.readline().strip()
                    if first_line.startswith('#!/bin/bash'):
                        self.log("   ✅ Valid shell script format")
                        return True, download_path
                    else:
                        self.log(f"   ❌ Invalid shell script format: {first_line}", "ERROR")
                        
            else:
                self.log(f"❌ Download Executable - Status: {response.status_code}", "FAIL")
                
        except Exception as e:
            self.log(f"❌ Download Executable - Error: {str(e)}", "FAIL")
            
        self.tests_run += 1
        return False, None

    def test_executable_verification(self, executable_path):
        """Test if the downloaded executable actually works"""
        if not executable_path or not os.path.exists(executable_path):
            self.log("❌ No executable file to test", "ERROR")
            return False
            
        try:
            self.log("🔍 Testing Executable Verification...")
            
            # Check if Node.js is available
            import subprocess
            node_check = subprocess.run(['which', 'node'], capture_output=True, text=True)
            if node_check.returncode != 0:
                self.log("⚠️  Node.js not found - skipping executable test", "WARN")
                return True  # Not a failure, just can't test
                
            # Try to run the executable
            result = subprocess.run([executable_path], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                self.tests_passed += 1
                self.log("✅ Executable Verification - Runs successfully", "PASS")
                self.log(f"   Output preview: {result.stdout[:200]}...")
                return True
            else:
                self.log(f"❌ Executable failed with return code: {result.returncode}", "FAIL")
                self.log(f"   Error: {result.stderr[:200]}", "ERROR")
                
        except subprocess.TimeoutExpired:
            self.log("❌ Executable timed out", "FAIL")
        except Exception as e:
            self.log(f"❌ Executable Verification - Error: {str(e)}", "FAIL")
            
        self.tests_run += 1
        return False

    def test_get_all_jobs(self):
        """Test getting all jobs after conversion"""
        success, response = self.run_test(
            "Get All Jobs",
            "GET",
            "jobs",
            200
        )
        if success:
            self.log(f"   Found {len(response)} total jobs")
            if self.current_job_id:
                job_found = any(job.get('id') == self.current_job_id for job in response)
                if job_found:
                    self.log("   ✅ Current job found in jobs list")
                else:
                    self.log("   ❌ Current job not found in jobs list", "ERROR")
        return success

    def test_delete_job(self):
        """Test job deletion"""
        if not self.current_job_id:
            self.log("❌ No job ID available for deletion", "ERROR")
            return False
            
        success, response = self.run_test(
            "Delete Job",
            "DELETE",
            f"jobs/{self.current_job_id}",
            200
        )
        
        if success:
            self.log(f"   Deleted job: {self.current_job_id}")
        return success

    def run_all_tests(self):
        """Run all API tests"""
        self.log("🚀 Starting TS2JS2dotSH API Tests...")
        self.log(f"   Base URL: {self.base_url}")
        self.log(f"   API URL: {self.api_url}")
        
        # Test sequence
        tests = [
            ("API Root", self.test_api_root),
            ("Get Jobs (Initial)", self.test_get_jobs_empty),
            ("Convert Project", self.test_convert_project),
            ("Wait for Completion", lambda: self.wait_for_job_completion()[0]),
            ("Download Executable", lambda: self.test_download_executable()[0]),
            ("Get All Jobs", self.test_get_all_jobs),
        ]
        
        executable_path = None
        
        for test_name, test_func in tests:
            self.log(f"\n--- {test_name} ---")
            
            if test_name == "Download Executable":
                success, path = self.test_download_executable()
                executable_path = path
            else:
                success = test_func()
                
            if not success and test_name in ["API Root", "Convert Project"]:
                self.log(f"❌ Critical test failed: {test_name}. Stopping tests.", "ERROR")
                break
                
        # Test executable if we have one
        if executable_path:
            self.log(f"\n--- Executable Verification ---")
            self.test_executable_verification(executable_path)
            
        # Optional cleanup
        if self.current_job_id:
            self.log(f"\n--- Cleanup ---")
            self.test_delete_job()

        # Print results
        self.log(f"\n📊 Test Results:")
        self.log(f"   Tests Run: {self.tests_run}")
        self.log(f"   Tests Passed: {self.tests_passed}")
        self.log(f"   Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        return self.tests_passed == self.tests_run

def main():
    tester = TS2JS2dotSHAPITester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())