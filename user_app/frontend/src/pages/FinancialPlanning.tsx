import React, { useState } from 'react';
import { useQuery, useMutation } from 'react-query';
import axios from 'axios';

interface FinancialData {
  income: number;
  expenses: number;
  savings: number;
  investments: number;
}

interface TokenFlow {
  original_token: {
    decoded: any;
    message: string;
  };
  token_exchange: {
    request: {
      grant_type: string;
      audience: string;
      scope: string;
    };
    response: any;
    message: string;
  };
  agent_tax_optimizer: {
    response: any;
    message: string;
  };
}

interface PlanningResult {
  message: string;
  token_flow: TokenFlow;
  optimization_result: {
    estimated_savings: number;
    recommendations: string[];
  };
}

const TokenFlowView: React.FC<{ tokenFlow: TokenFlow }> = ({ tokenFlow }) => {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="mt-4">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center text-sm font-medium text-blue-600 hover:text-blue-500"
      >
        <span>{expanded ? '▼' : '▶'} Token Flow Details</span>
      </button>
      
      {expanded && (
        <div className="mt-4 space-y-4">
          {/* Original Token */}
          <div>
            <h4 className="text-sm font-medium text-gray-500">1. Original User Token</h4>
            <p className="text-sm text-gray-600">{tokenFlow.original_token.message}</p>
            <pre className="mt-1 bg-gray-50 p-4 rounded-md overflow-x-auto">
              {JSON.stringify(tokenFlow.original_token.decoded, null, 2)}
            </pre>
          </div>

          {/* Token Exchange */}
          <div>
            <h4 className="text-sm font-medium text-gray-500">2. Token Exchange</h4>
            <p className="text-sm text-gray-600">{tokenFlow.token_exchange.message}</p>
            <div className="mt-2 space-y-2">
              <div>
                <p className="text-xs text-gray-500">Request:</p>
                <pre className="mt-1 bg-gray-50 p-4 rounded-md overflow-x-auto">
                  {JSON.stringify(tokenFlow.token_exchange.request, null, 2)}
                </pre>
              </div>
              <div>
                <p className="text-xs text-gray-500">Response:</p>
                <pre className="mt-1 bg-gray-50 p-4 rounded-md overflow-x-auto">
                  {JSON.stringify(tokenFlow.token_exchange.response, null, 2)}
                </pre>
              </div>
            </div>
          </div>

          {/* Tax Optimizer Response */}
          <div>
            <h4 className="text-sm font-medium text-gray-500">3. Tax Optimizer Response</h4>
            <p className="text-sm text-gray-600">{tokenFlow.agent_tax_optimizer.message}</p>
            <pre className="mt-1 bg-gray-50 p-4 rounded-md overflow-x-auto">
              {JSON.stringify(tokenFlow.agent_tax_optimizer.response, null, 2)}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
};

const FinancialPlanning: React.FC = () => {
  const [financialData, setFinancialData] = useState<FinancialData>({
    income: 0,
    expenses: 0,
    savings: 0,
    investments: 0,
  });

  const { data: planningResult, refetch: refetchPlanning } = useQuery<PlanningResult>(
    'financial-planning',
    async () => {
      console.log('Making request to /api/financial-planning with data:', financialData);
      try {
        const response = await axios.post('/api/financial-planning', financialData);
        console.log('Received response:', response.data);
        return response.data;
      } catch (error) {
        console.error('Error making request:', error);
        throw error;
      }
    },
    { enabled: false }
  );

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFinancialData(prev => ({
      ...prev,
      [name]: parseFloat(value) || 0
    }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    console.log('Form submitted with data:', financialData);
    refetchPlanning();
  };

  console.log('Current planningResult:', planningResult);

  return (
    <div className="space-y-6">
      <div className="bg-white shadow sm:rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900">
            Financial Planning
          </h3>
          
          <form onSubmit={handleSubmit} className="mt-5 space-y-4">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <label htmlFor="income" className="block text-sm font-medium text-gray-700">
                  Annual Income
                </label>
                <input
                  type="number"
                  name="income"
                  id="income"
                  value={financialData.income}
                  onChange={handleInputChange}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                />
              </div>

              <div>
                <label htmlFor="expenses" className="block text-sm font-medium text-gray-700">
                  Monthly Expenses
                </label>
                <input
                  type="number"
                  name="expenses"
                  id="expenses"
                  value={financialData.expenses}
                  onChange={handleInputChange}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                />
              </div>

              <div>
                <label htmlFor="savings" className="block text-sm font-medium text-gray-700">
                  Current Savings
                </label>
                <input
                  type="number"
                  name="savings"
                  id="savings"
                  value={financialData.savings}
                  onChange={handleInputChange}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                />
              </div>

              <div>
                <label htmlFor="investments" className="block text-sm font-medium text-gray-700">
                  Current Investments
                </label>
                <input
                  type="number"
                  name="investments"
                  id="investments"
                  value={financialData.investments}
                  onChange={handleInputChange}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                />
              </div>
            </div>

            <div>
              <button
                type="submit"
                className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                Generate Financial Plan
              </button>
            </div>
          </form>
        </div>
      </div>

      {planningResult && (
        <div className="space-y-6">
          <div className="bg-white shadow sm:rounded-lg">
            <div className="px-4 py-5 sm:p-6">
              <h3 className="text-lg leading-6 font-medium text-gray-900">
                Response
              </h3>
              <div className="mt-4 space-y-4">
                <div>
                  <h4 className="text-sm font-medium text-gray-500">Message</h4>
                  <p className="text-sm text-gray-600">{planningResult.message}</p>
                </div>

                {planningResult.optimization_result && (
                  <div>
                    <h4 className="text-sm font-medium text-gray-500">Optimization Results</h4>
                    <div className="mt-2 bg-gray-50 p-4 rounded-md">
                      <p className="text-sm text-gray-600">
                        Estimated Savings: ${planningResult.optimization_result.estimated_savings}
                      </p>
                      <ul className="mt-2 list-disc pl-5 space-y-1">
                        {planningResult.optimization_result.recommendations.map((rec, index) => (
                          <li key={index} className="text-sm text-gray-600">{rec}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                )}

                {planningResult.token_flow && (
                  <TokenFlowView tokenFlow={planningResult.token_flow} />
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default FinancialPlanning; 