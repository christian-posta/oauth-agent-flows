import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

const Login: React.FC = () => {
  const navigate = useNavigate();

  useEffect(() => {
    const checkAuth = async () => {
      try {
        const response = await axios.get('/api/user');
        if (response.data) {
          navigate('/');
        }
      } catch (error) {
        // User is not authenticated
      }
    };
    checkAuth();
  }, [navigate]);

  const handleLogin = () => {
    window.location.href = 'http://localhost:8000/login';
  };

  return (
    <div className="min-h-screen bg-gray-100 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
          AI Agent Demo
        </h2>
        <p className="mt-2 text-center text-sm text-gray-600">
          Secure Financial Planning with AI Agents
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
          <div>
            <button
              onClick={handleLogin}
              className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              Sign in with Keycloak
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login; 