import React, { useState } from 'react';

const FileUpload = ({ onUpload }) => {
  const [files, setFiles] = useState([]);
  const [isDragOver, setIsDragOver] = useState(false);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      const newFiles = Array.from(e.target.files);
      setFiles(prevFiles => [...prevFiles, ...newFiles]);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = () => {
    setIsDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const newFiles = Array.from(e.dataTransfer.files);
      setFiles(prevFiles => [...prevFiles, ...newFiles]);
    }
  };

  const removeFile = (index) => {
    setFiles(prevFiles => prevFiles.filter((_, i) => i !== index));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (files.length > 0) {
      onUpload(files);
      setFiles([]);
    }
  };

  return (
    <div>
      <h2>Upload Citizen Documents</h2>
      <p>Upload PDF documents containing citizen information</p>
      
      <form onSubmit={handleSubmit}>
        <div 
          className={`file-upload ${isDragOver ? 'dragover' : ''}`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          <p>Drag and drop PDF files here, or click to select files</p>
          <div className="file-input">
            <input
              type="file"
              id="fileInput"
              accept=".pdf"
              multiple
              onChange={handleFileChange}
            />
            <label htmlFor="fileInput">Choose Files</label>
          </div>
          {files.length > 0 && (
            <div className="selected-files">
              <h3>Selected Files:</h3>
              <ul>
                {files.map((file, index) => (
                  <li key={index}>
                    {file.name}
                    <button 
                      type="button" 
                      className="btn-remove"
                      onClick={() => removeFile(index)}
                    >
                      Remove
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
        
        <button 
          type="submit" 
          className="btn upload-button"
          disabled={files.length === 0}
        >
          Upload Documents
        </button>
      </form>
    </div>
  );
};

export default FileUpload;