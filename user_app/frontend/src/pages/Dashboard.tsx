import React from 'react';
import { Link } from 'react-router-dom';

const Dashboard: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="bg-white shadow sm:rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900">
            Welcome to AI Agent Demo
          </h3>
          <div className="mt-2 max-w-xl text-sm text-gray-500">
            <p>
              This demo showcases secure delegation chains in financial processing using AI agents.
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
        <Link
          to="/financial-planning"
          className="bg-white overflow-hidden shadow rounded-lg hover:shadow-lg transition-shadow duration-300"
        >
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg font-medium text-gray-900">Financial Planning</h3>
            <p className="mt-1 text-sm text-gray-500">
              Access your financial planning tools and AI agent assistance
            </p>
          </div>
        </Link>

        <Link
          to="/tokens"
          className="bg-white overflow-hidden shadow rounded-lg hover:shadow-lg transition-shadow duration-300"
        >
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg font-medium text-gray-900">Token Information</h3>
            <p className="mt-1 text-sm text-gray-500">
              View and analyze your authentication tokens and delegation chains
            </p>
          </div>
        </Link>

        <Link
          to="/a2a-flow"
          className="bg-white overflow-hidden shadow rounded-lg hover:shadow-lg transition-shadow duration-300"
        >
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg font-medium text-gray-900">A2A Flow</h3>
            <p className="mt-1 text-sm text-gray-500">
              Monitor real-time agent-to-agent communication flows
            </p>
          </div>
        </Link>
      </div>
    </div>
  );
};

export default Dashboard; 