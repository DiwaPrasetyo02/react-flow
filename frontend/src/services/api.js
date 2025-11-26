import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const executeAgent = async (agentType, data) => {
  try {
    const response = await api.post(`/agents/${agentType}/execute`, data);
    return response.data;
  } catch (error) {
    console.error(`Error executing ${agentType} agent:`, error);
    throw error;
  }
};

export const uploadFile = async (file, description = '') => {
  try {
    const formData = new FormData();
    formData.append('file', file);
    if (description) {
      formData.append('description', description);
    }
    
    const response = await axios.post(`${API_BASE_URL}/files/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  } catch (error) {
    console.error('Error uploading file:', error);
    throw error;
  }
};

export const getDocument = async (documentId) => {
  try {
    const response = await api.get(`/files/documents/${documentId}`);
    return response.data;
  } catch (error) {
    console.error('Error getting document:', error);
    throw error;
  }
};

export const getAgentStatus = async (taskId) => {
  try {
    const response = await api.get(`/tasks/${taskId}`);
    return response.data;
  } catch (error) {
    console.error('Error getting task status:', error);
    throw error;
  }
};

export default api;
