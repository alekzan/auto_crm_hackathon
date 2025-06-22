const API_BASE_URL = import.meta.env.VITE_API_URL !== undefined
    ? import.meta.env.VITE_API_URL
    : 'http://localhost:8001';

export default API_BASE_URL; 