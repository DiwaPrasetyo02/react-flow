import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

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
