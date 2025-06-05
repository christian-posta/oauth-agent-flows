import React from 'react';
import { useQuery } from 'react-query';
import axios from 'axios';

interface Agent {
  id: string;
  name: string;
  capabilities: string[];
  status: string;
  last_seen: string;
  health?: {
    status: string;
    uptime_percentage: number;
  };
}

const Agents: React.FC = () => {
  const { data: agentsData, isLoading, error } = useQuery<{ agents: Agent[]; timestamp: string }>(
    'agents',
    async () => {
      const response = await axios.get('/api/agents');
      return response.data;
    },
    {
      refetchInterval: 30000, // Refresh every 30 seconds
    }
  );

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-32">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
        Error loading agent information
      </div>
    );
  }

  return (
    <div>
      <div className="px-4 py-5 sm:px-6">
        <h3 className="text-lg leading-6 font-medium text-gray-900">Agent Status</h3>
        <p className="mt-1 max-w-2xl text-sm text-gray-500">Current status of all registered agents.</p>
      </div>
      <div className="bg-white shadow overflow-hidden sm:rounded-lg">
        <ul role="list" className="divide-y divide-gray-200">
          {agentsData?.agents.map((agent) => (
            <li key={agent.id} className="px-4 py-4 sm:px-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <div className="h-10 w-10 rounded-full bg-indigo-100 flex items-center justify-center">
                      <span className="text-indigo-600 font-medium">{agent.name[0]}</span>
                    </div>
                  </div>
                  <div className="ml-4">
                    <div className="text-sm font-medium text-gray-900">{agent.name}</div>
                    <div className="text-sm text-gray-500">ID: {agent.id}</div>
                  </div>
                </div>
                <div className="flex items-center">
                  <span
                    className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                      agent.status === 'active'
                        ? 'bg-green-100 text-green-800'
                        : 'bg-red-100 text-red-800'
                    }`}
                  >
                    {agent.status}
                  </span>
                </div>
              </div>
              <div className="mt-2">
                <div className="text-sm text-gray-500">
                  <strong>Capabilities:</strong>
                  <div className="mt-1 flex flex-wrap gap-2">
                    {agent.capabilities.map((capability) => (
                      <span
                        key={capability}
                        className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                      >
                        {capability}
                      </span>
                    ))}
                  </div>
                </div>
                <div className="mt-2 text-sm text-gray-500">
                  <strong>Last Seen:</strong>{' '}
                  {new Date(agent.last_seen).toLocaleString()}
                </div>
                {agent.health && (
                  <div className="mt-2 text-sm text-gray-500">
                    <strong>Health:</strong>
                    <div className="mt-1">
                      <div className="flex items-center">
                        <div className="w-full bg-gray-200 rounded-full h-2.5">
                          <div
                            className="bg-green-600 h-2.5 rounded-full"
                            style={{ width: `${agent.health.uptime_percentage}%` }}
                          ></div>
                        </div>
                        <span className="ml-2 text-xs text-gray-500">
                          {agent.health.uptime_percentage}% uptime
                        </span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </li>
          ))}
        </ul>
        <div className="px-4 py-3 bg-gray-50 text-right text-sm text-gray-500">
          Last updated: {new Date(agentsData?.timestamp || '').toLocaleString()}
        </div>
      </div>
    </div>
  );
};

export default Agents; 