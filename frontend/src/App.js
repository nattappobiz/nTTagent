import React, { useState } from 'react';
import './App.css';
import CitizenList from './components/CitizenList';
import FileUpload from './components/FileUpload';
import ApiService from './services/ApiService';

function App() {
  const [activeTab, setActiveTab] = useState('citizens');
  const [citizens, setCitizens] = useState([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });

  const showMessage = (text, type = 'success') => {
    setMessage({ text, type });
    setTimeout(() => setMessage({ text: '', type: '' }), 5000);
  };

  const fetchCitizens = async () => {
    setLoading(true);
    try {
      const data = await ApiService.getCitizens();
      setCitizens(data);
      showMessage('Citizens loaded successfully', 'success');
    } catch (error) {
      showMessage('Failed to load citizens', 'error');
      console.error('Error fetching citizens:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (files) => {
    try {
      await ApiService.uploadFiles(files);
      showMessage('Files uploaded successfully', 'success');
      // Refresh citizens list after upload
      fetchCitizens();
    } catch (error) {
      showMessage('Failed to upload files', 'error');
      console.error('Error uploading files:', error);
    }
  };

  return (
    <div className="App">
      <header className="header">
        <h1>ElderDocs</h1>
        <p>Document Management System</p>
      </header>

      <div className="container">
        {message.text && (
          <div className={`alert alert-${message.type}`}>
            {message.text}
          </div>
        )}

        <div className="tabs">
          <button 
            className={activeTab === 'citizens' ? 'tab active' : 'tab'}
            onClick={() => setActiveTab('citizens')}
          >
            Citizens
          </button>
          <button 
            className={activeTab === 'upload' ? 'tab active' : 'tab'}
            onClick={() => setActiveTab('upload')}
          >
            Upload Documents
          </button>
        </div>

        <div className="main-content">
          {activeTab === 'citizens' && (
            <CitizenList 
              citizens={citizens} 
              loading={loading}
              onRefresh={fetchCitizens}
            />
          )}
          
          {activeTab === 'upload' && (
            <FileUpload onUpload={handleFileUpload} />
          )}
        </div>
      </div>
    </div>
  );
}

export default App;