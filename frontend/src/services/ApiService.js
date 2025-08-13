import axios from 'axios';

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000', // Backend URL from environment
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

class ApiService {
  // Get all citizens
  static async getCitizens() {
    try {
      const response = await apiClient.get('/files');
      return response.data;
    } catch (error) {
      console.error('Error fetching citizens:', error);
      throw error;
    }
  }

  // Get citizens by status
  static async getCitizensByStatus(status) {
    try {
      const response = await apiClient.get(`/files?status=${status}`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching citizens with status ${status}:`, error);
      throw error;
    }
  }

  // Upload files
  static async uploadFiles(files) {
    try {
      const formData = new FormData();
      files.forEach(file => {
        formData.append('files', file);
      });
      
      const response = await apiClient.post('/uploads', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      
      return response.data;
    } catch (error) {
      console.error('Error uploading files:', error);
      throw error;
    }
  }

  // Get citizen by ID
  static async getCitizenById(id) {
    try {
      const response = await apiClient.get(`/citizens/${id}`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching citizen ${id}:`, error);
      throw error;
    }
  }

  // Update citizen
  static async updateCitizen(id, data) {
    try {
      const response = await apiClient.put(`/citizens/${id}`, data);
      return response.data;
    } catch (error) {
      console.error(`Error updating citizen ${id}:`, error);
      throw error;
    }
  }

  // Export data
  static async exportData() {
    try {
      const response = await apiClient.get('/export');
      return response.data;
    } catch (error) {
      console.error('Error exporting data:', error);
      throw error;
    }
  }
}

export default ApiService;