import React, { useState, useRef } from 'react';
import { uploadFile } from '../services/api';
import './FileUpload.css';

const FileUpload = ({ onFileUpload, acceptedFormats = '.pdf,.csv,.doc,.docx,.txt,.jpg,.jpeg,.png' }) => {
  const [dragActive, setDragActive] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef(null);

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

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFiles(e.dataTransfer.files);
    }
  };

  const handleChange = (e) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      handleFiles(e.target.files);
    }
  };

  const handleFiles = async (files) => {
    setUploading(true);
    const fileArray = Array.from(files);

    try {
      const results = [];
      for (const file of fileArray) {
        try {
          // Upload file to backend
          const uploadResult = await uploadFile(file);
          
          const fileData = {
            name: file.name,
            size: file.size,
            type: file.type,
            document_id: uploadResult.document_id,
            file_path: uploadResult.file_path,
            uploadedAt: new Date().toISOString(),
            uploadResult: uploadResult,
          };
          results.push(fileData);
        } catch (error) {
          console.error(`Error uploading ${file.name}:`, error);
          // Still add file to list but mark as failed
          results.push({
            name: file.name,
            size: file.size,
            type: file.type,
            error: error.message || 'Upload failed',
            uploadedAt: new Date().toISOString(),
          });
        }
      }

      setUploadedFiles((prev) => [...prev, ...results]);

      if (onFileUpload) {
        await onFileUpload(results);
      }
    } catch (error) {
      console.error('Error handling files:', error);
    } finally {
      setUploading(false);
    }
  };

  const removeFile = (index) => {
    setUploadedFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  const getFileIcon = (fileName) => {
    const extension = fileName.split('.').pop().toLowerCase();
    const icons = {
      pdf: '📕',
      csv: '📊',
      doc: '📘',
      docx: '📘',
      txt: '📝',
      xls: '📗',
      xlsx: '📗',
    };
    return icons[extension] || '📄';
  };

  return (
    <div className="file-upload-container">
      <form
        className={`file-upload-form ${dragActive ? 'drag-active' : ''}`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onSubmit={(e) => e.preventDefault()}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          onChange={handleChange}
          accept={acceptedFormats}
          style={{ display: 'none' }}
        />

        <div className="upload-content">
          <div className="upload-icon">📁</div>
          <h3>Upload Documents</h3>
          <p>Drag and drop your files here, or click to browse</p>
          <p className="upload-formats">Supported: PDF, CSV, Word, TXT</p>
          <button
            type="button"
            className="browse-btn"
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading}
          >
            {uploading ? 'Uploading...' : 'Browse Files'}
          </button>
        </div>
      </form>

      {uploadedFiles.length > 0 && (
        <div className="uploaded-files">
          <h4>Uploaded Files ({uploadedFiles.length})</h4>
          <div className="files-list">
            {uploadedFiles.map((file, index) => (
              <div key={index} className="file-item">
                <span className="file-icon">{getFileIcon(file.name)}</span>
                <div className="file-info">
                  <p className="file-name">{file.name}</p>
                  <p className="file-size">{formatFileSize(file.size)}</p>
                </div>
                <button
                  className="remove-btn"
                  onClick={() => removeFile(index)}
                  title="Remove file"
                >
                  ✕
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default FileUpload;
