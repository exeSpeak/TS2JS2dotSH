import React, { useState, useEffect, useRef } from 'react';
import './App.css';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const App = () => {
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [projectName, setProjectName] = useState('');
  const [currentJob, setCurrentJob] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [dragActive, setDragActive] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef(null);
  const statusIntervalRef = useRef(null);

  // Fetch all jobs on component mount
  useEffect(() => {
    fetchJobs();
  }, []);

  // Poll job status if there's a current job
  useEffect(() => {
    if (currentJob && (currentJob.status === 'pending' || currentJob.status === 'processing')) {
      statusIntervalRef.current = setInterval(() => {
        checkJobStatus(currentJob.job_id);
      }, 2000);
    } else {
      if (statusIntervalRef.current) {
        clearInterval(statusIntervalRef.current);
      }
    }

    return () => {
      if (statusIntervalRef.current) {
        clearInterval(statusIntervalRef.current);
      }
    };
  }, [currentJob]);

  const fetchJobs = async () => {
    try {
      const response = await axios.get(`${API}/jobs`);
      setJobs(response.data);
    } catch (error) {
      console.error('Failed to fetch jobs:', error);
    }
  };

  const checkJobStatus = async (jobId) => {
    try {
      const response = await axios.get(`${API}/status/${jobId}`);
      setCurrentJob(response.data);
      
      if (response.data.status === 'completed' || response.data.status === 'failed') {
        fetchJobs(); // Refresh the jobs list
      }
    } catch (error) {
      console.error('Failed to check job status:', error);
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    const files = Array.from(e.dataTransfer.files);
    setSelectedFiles(files);
  };

  const handleFileSelect = (e) => {
    const files = Array.from(e.target.files);
    setSelectedFiles(files);
  };

  const removeFile = (index) => {
    const newFiles = selectedFiles.filter((_, i) => i !== index);
    setSelectedFiles(newFiles);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!projectName.trim()) {
      alert('Please enter a project name');
      return;
    }
    
    if (selectedFiles.length === 0) {
      alert('Please select at least one TypeScript file');
      return;
    }

    setIsUploading(true);
    
    try {
      const formData = new FormData();
      formData.append('project_name', projectName);
      
      selectedFiles.forEach((file) => {
        formData.append('files', file);
      });

      const response = await axios.post(`${API}/convert`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setCurrentJob(response.data);
      setSelectedFiles([]);
      setProjectName('');
      
    } catch (error) {
      console.error('Upload failed:', error);
      alert('Upload failed: ' + (error.response?.data?.detail || error.message));
    } finally {
      setIsUploading(false);
    }
  };

  const downloadFile = (jobId) => {
    window.open(`${API}/download/${jobId}`, '_blank');
  };

  const deleteJob = async (jobId) => {
    if (window.confirm('Are you sure you want to delete this job?')) {
      try {
        await axios.delete(`${API}/jobs/${jobId}`);
        fetchJobs();
        if (currentJob && currentJob.job_id === jobId) {
          setCurrentJob(null);
        }
      } catch (error) {
        console.error('Failed to delete job:', error);
        alert('Failed to delete job');
      }
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'text-green-600 bg-green-100';
      case 'failed':
        return 'text-red-600 bg-red-100';
      case 'processing':
        return 'text-blue-600 bg-blue-100';
      default:
        return 'text-yellow-600 bg-yellow-100';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold text-white mb-4">
            TS2JS2<span className="text-purple-400">.sh</span>
          </h1>
          <p className="text-xl text-gray-300 mb-2">
            Convert TypeScript Projects to Executable Shell Scripts
          </p>
          <p className="text-sm text-gray-400">
            Transform your TypeScript code into clickable Linux executables
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Upload Section */}
          <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-8 border border-white/20">
            <h2 className="text-2xl font-bold text-white mb-6">Upload Your Project</h2>
            
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Project Name Input */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Project Name
                </label>
                <input
                  type="text"
                  value={projectName}
                  onChange={(e) => setProjectName(e.target.value)}
                  className="w-full px-4 py-3 bg-white/5 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500"
                  placeholder="Enter your project name"
                  required
                />
              </div>

              {/* File Upload Area */}
              <div
                className={`relative border-2 border-dashed rounded-lg p-8 transition-colors ${
                  dragActive
                    ? 'border-purple-500 bg-purple-500/10'
                    : 'border-white/30 hover:border-white/50'
                }`}
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  multiple
                  onChange={handleFileSelect}
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                  accept=".ts,.tsx,.js,.jsx,.json"
                />
                
                <div className="text-center">
                  <div className="mx-auto w-12 h-12 bg-purple-500/20 rounded-lg flex items-center justify-center mb-4">
                    <svg className="w-6 h-6 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                    </svg>
                  </div>
                  <p className="text-lg text-white mb-2">
                    Drop your TypeScript files here
                  </p>
                  <p className="text-sm text-gray-400 mb-4">
                    or click to browse files
                  </p>
                  <p className="text-xs text-gray-500">
                    Supports .ts, .tsx, .js, .jsx, .json files
                  </p>
                </div>
              </div>

              {/* Selected Files List */}
              {selectedFiles.length > 0 && (
                <div className="space-y-3">
                  <h3 className="text-sm font-medium text-gray-300">Selected Files</h3>
                  <div className="space-y-2 max-h-40 overflow-y-auto">
                    {selectedFiles.map((file, index) => (
                      <div key={index} className="flex items-center justify-between bg-white/5 rounded-lg p-3">
                        <div className="flex items-center space-x-3">
                          <div className="w-8 h-8 bg-purple-500/20 rounded flex items-center justify-center">
                            <svg className="w-4 h-4 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                            </svg>
                          </div>
                          <div>
                            <p className="text-sm text-white">{file.name}</p>
                            <p className="text-xs text-gray-400">{formatFileSize(file.size)}</p>
                          </div>
                        </div>
                        <button
                          type="button"
                          onClick={() => removeFile(index)}
                          className="text-red-400 hover:text-red-300 transition-colors"
                        >
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                          </svg>
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Submit Button */}
              <button
                type="submit"
                disabled={isUploading || selectedFiles.length === 0 || !projectName.trim()}
                className="w-full bg-gradient-to-r from-purple-600 to-pink-600 text-white py-3 px-6 rounded-lg font-medium transition-all duration-200 hover:from-purple-700 hover:to-pink-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isUploading ? (
                  <div className="flex items-center justify-center space-x-2">
                    <svg className="animate-spin w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                    <span>Converting...</span>
                  </div>
                ) : (
                  'Convert to Shell Executable'
                )}
              </button>
            </form>
          </div>

          {/* Status and Jobs Section */}
          <div className="space-y-6">
            {/* Current Job Status */}
            {currentJob && (
              <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 border border-white/20">
                <h3 className="text-xl font-bold text-white mb-4">Current Job Status</h3>
                
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-gray-300">Job ID:</span>
                    <span className="text-white font-mono text-sm">{currentJob.job_id}</span>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <span className="text-gray-300">Status:</span>
                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(currentJob.status)}`}>
                      {currentJob.status.toUpperCase()}
                    </span>
                  </div>
                  
                  {currentJob.progress !== undefined && (
                    <div>
                      <div className="flex justify-between text-sm text-gray-300 mb-1">
                        <span>Progress</span>
                        <span>{currentJob.progress}%</span>
                      </div>
                      <div className="w-full bg-white/10 rounded-full h-2">
                        <div 
                          className="bg-gradient-to-r from-purple-600 to-pink-600 h-2 rounded-full transition-all duration-500"
                          style={{ width: `${currentJob.progress}%` }}
                        ></div>
                      </div>
                    </div>
                  )}
                  
                  {currentJob.error_message && (
                    <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-3">
                      <p className="text-red-400 text-sm">{currentJob.error_message}</p>
                    </div>
                  )}
                  
                  {currentJob.download_url && (
                    <button
                      onClick={() => downloadFile(currentJob.job_id)}
                      className="w-full bg-gradient-to-r from-green-600 to-emerald-600 text-white py-2 px-4 rounded-lg font-medium transition-all duration-200 hover:from-green-700 hover:to-emerald-700"
                    >
                      Download Executable
                    </button>
                  )}
                </div>
              </div>
            )}

            {/* Jobs History */}
            <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 border border-white/20">
              <h3 className="text-xl font-bold text-white mb-4">Recent Jobs</h3>
              
              {jobs.length === 0 ? (
                <p className="text-gray-400 text-center py-8">No jobs yet</p>
              ) : (
                <div className="space-y-3 max-h-80 overflow-y-auto">
                  {jobs.map((job) => (
                    <div key={job.id} className="bg-white/5 rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="text-white font-medium">{job.project_name}</h4>
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(job.status)}`}>
                          {job.status}
                        </span>
                      </div>
                      
                      <p className="text-gray-400 text-xs mb-3">
                        {new Date(job.created_at).toLocaleString()}
                      </p>
                      
                      <div className="flex space-x-2">
                        {job.status === 'completed' && (
                          <button
                            onClick={() => downloadFile(job.id)}
                            className="flex-1 bg-green-600 hover:bg-green-700 text-white py-1 px-3 rounded text-sm transition-colors"
                          >
                            Download
                          </button>
                        )}
                        <button
                          onClick={() => deleteJob(job.id)}
                          className="flex-1 bg-red-600 hover:bg-red-700 text-white py-1 px-3 rounded text-sm transition-colors"
                        >
                          Delete
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="text-center mt-12 pt-8 border-t border-white/10">
          <p className="text-gray-400 text-sm">
            TS2JS2dotSH Converter - Transform your TypeScript projects into executable shell scripts
          </p>
        </div>
      </div>
    </div>
  );
};

export default App;