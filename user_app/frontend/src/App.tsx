import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useQuery } from 'react-query';
import axios from 'axios';
import { useAuth } from './contexts/AuthContext';

// Pages
import Dashboard from './pages/Dashboard';
import Login from './pages/Login';
import FinancialPlanning from './pages/FinancialPlanning';
import TokenVisualization from './pages/TokenVisualization';
import A2AFlow from './pages/A2AFlow';
import Agents from './pages/Agents';

// Components
import Layout from './components/Layout';
import ProtectedRoute from './components/ProtectedRoute';

const App: React.FC = () => {
  const { user } = useAuth();
  const { data: userData, isLoading, error } = useQuery('user', async () => {
    try {
      const response = await axios.get('/api/user');
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response?.status === 401) {
        // 401 is expected when not logged in
        return null;
      }
      console.error('Error fetching user:', error);
      throw error;
    }
  }, {
    retry: false,
    refetchOnWindowFocus: false,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-xl text-gray-600">Loading...</div>
      </div>
    );
  }

  // If there's no user, show the login page
  if (!user) {
    return <Login />;
  }

  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/"
        element={
          <ProtectedRoute user={user}>
            <Layout user={user} />
          </ProtectedRoute>
        }
      >
        <Route index element={<Dashboard />} />
        <Route path="financial-planning" element={<FinancialPlanning />} />
        <Route path="agents" element={<Agents />} />
        <Route path="tokens" element={<TokenVisualization />} />
        <Route path="a2a-flow" element={<A2AFlow />} />
      </Route>
    </Routes>
  );
};

export default App; 