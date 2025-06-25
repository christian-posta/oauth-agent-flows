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
    decoded_token?: any;
    message: string;
  };
  agent_tax_optimizer: {
    original_token?: {
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
      decoded_token?: any;
      message: string;
    };
    calculator_response: {
      message: string;
      tax_result: any;
    };
    response: any;
    message: string;
  };
}

interface PlanningResult {
  message: string;
  token_flow: TokenFlow;
  optimization_result: {
    estimated_savings: number;
    monthly_savings_potential?: number;
    current_tax_burden?: number;
    effective_tax_rate?: number;
    retirement_impact?: number;
    recommendations: string[];
    financial_summary?: {
      annual_income: number;
      annual_expenses: number;
      current_savings: number;
      current_investments: number;
      savings_rate: number;
      tax_efficiency_score?: number;
      investment_diversification?: number;
      emergency_fund_coverage?: number;
    };
    optimization_confidence?: number;
    time_to_implement?: number;
    priority_score?: number;
  };
}

const TokenFlowView: React.FC<{ tokenFlow: TokenFlow }> = ({ tokenFlow }) => {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="mt-4">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center text-sm font-medium text-gray-600 hover:text-gray-500"
      >
        <span>{expanded ? '▼' : '▶'} Technical Details (Token Flow)</span>
      </button>
      
      {expanded && (
        <div className="mt-4 space-y-6">
          {/* User App Section */}
          <div className="border border-gray-200 rounded-lg p-4">
            <h4 className="text-lg font-semibold text-gray-800 mb-3">1. User Application</h4>
            <p className="text-sm text-gray-600 mb-3">The user's original token that was sent to the Agent Planner</p>
            <div className="bg-gray-50 p-3 rounded-md">
              <p className="text-xs text-gray-500 mb-2">Original User Token:</p>
              <pre className="text-xs overflow-x-auto">
                {JSON.stringify(tokenFlow.original_token.decoded, null, 2)}
              </pre>
            </div>
          </div>

          {/* Agent Planner Section */}
          <div className="border border-blue-200 rounded-lg p-4 bg-blue-50">
            <h4 className="text-lg font-semibold text-blue-800 mb-3">2. Agent Planner Service</h4>
            <p className="text-sm text-blue-600 mb-3">Received user token and exchanged it for Tax Optimizer access</p>
            
            <div className="space-y-3">
              <div>
                <p className="text-xs text-blue-500 mb-1">Received Token (from User):</p>
                <div className="bg-white p-3 rounded-md border border-blue-200">
                  <pre className="text-xs overflow-x-auto">
                    {JSON.stringify(tokenFlow.original_token.decoded, null, 2)}
                  </pre>
                </div>
              </div>
              
              <div>
                <p className="text-xs text-blue-500 mb-1">Token Exchange Request (for Tax Optimizer):</p>
                <div className="bg-white p-3 rounded-md border border-blue-200">
                  <pre className="text-xs overflow-x-auto">
                    {JSON.stringify(tokenFlow.token_exchange.request, null, 2)}
                  </pre>
                </div>
              </div>
              
              <div>
                <p className="text-xs text-blue-500 mb-1">Token Exchange Response:</p>
                <div className="bg-white p-3 rounded-md border border-blue-200">
                  <pre className="text-xs overflow-x-auto">
                    {JSON.stringify(tokenFlow.token_exchange.response, null, 2)}
                  </pre>
                </div>
              </div>
              
              <div>
                <p className="text-xs text-blue-500 mb-1">Decoded Exchanged Token:</p>
                <div className="bg-white p-3 rounded-md border border-blue-200">
                  <pre className="text-xs overflow-x-auto">
                    {JSON.stringify(tokenFlow.token_exchange.decoded_token || {}, null, 2)}
                  </pre>
                </div>
              </div>
              
              <div>
                <p className="text-xs text-blue-500 mb-1">Debug - Full Token Exchange Data:</p>
                <div className="bg-white p-3 rounded-md border border-blue-200">
                  <pre className="text-xs overflow-x-auto">
                    {JSON.stringify(tokenFlow.token_exchange, null, 2)}
                  </pre>
                </div>
              </div>
            </div>
          </div>

          {/* Tax Optimizer Section */}
          <div className="border border-green-200 rounded-lg p-4 bg-green-50">
            <h4 className="text-lg font-semibold text-green-800 mb-3">3. Tax Optimizer Service</h4>
            <p className="text-sm text-green-600 mb-3">Received planner token and exchanged it for Calculator access</p>
            
            <div className="space-y-3">
              <div>
                <p className="text-xs text-green-500 mb-1">Received Token (from Planner):</p>
                <div className="bg-white p-3 rounded-md border border-green-200">
                  <pre className="text-xs overflow-x-auto">
                    {JSON.stringify(tokenFlow.agent_tax_optimizer.original_token?.decoded || {}, null, 2)}
                  </pre>
                </div>
              </div>
              
              <div>
                <p className="text-xs text-green-500 mb-1">Token Exchange Request (for Calculator):</p>
                <div className="bg-white p-3 rounded-md border border-green-200">
                  <pre className="text-xs overflow-x-auto">
                    {JSON.stringify(tokenFlow.agent_tax_optimizer.token_exchange.request, null, 2)}
                  </pre>
                </div>
              </div>
              
              <div>
                <p className="text-xs text-green-500 mb-1">Token Exchange Response:</p>
                <div className="bg-white p-3 rounded-md border border-green-200">
                  <pre className="text-xs overflow-x-auto">
                    {JSON.stringify(tokenFlow.agent_tax_optimizer.token_exchange.response, null, 2)}
                  </pre>
                </div>
              </div>
              
              <div>
                <p className="text-xs text-green-500 mb-1">Decoded Exchanged Token:</p>
                <div className="bg-white p-3 rounded-md border border-green-200">
                  <pre className="text-xs overflow-x-auto">
                    {JSON.stringify(tokenFlow.agent_tax_optimizer.token_exchange.decoded_token || tokenFlow.agent_tax_optimizer.token_exchange?.decoded_token || {}, null, 2)}
                  </pre>
                </div>
              </div>
              
              <div>
                <p className="text-xs text-green-500 mb-1">Debug - Full Token Exchange Data:</p>
                <div className="bg-white p-3 rounded-md border border-green-200">
                  <pre className="text-xs overflow-x-auto">
                    {JSON.stringify(tokenFlow.agent_tax_optimizer.token_exchange, null, 2)}
                  </pre>
                </div>
              </div>
            </div>
          </div>

          {/* Calculator Section */}
          <div className="border border-purple-200 rounded-lg p-4 bg-purple-50">
            <h4 className="text-lg font-semibold text-purple-800 mb-3">4. Calculator Service</h4>
            <p className="text-sm text-purple-600 mb-3">Received tax optimizer token and processed the calculation</p>
            
            <div className="space-y-3">
              <div>
                <p className="text-xs text-purple-500 mb-1">Received Token (from Tax Optimizer):</p>
                <div className="bg-white p-3 rounded-md border border-purple-200">
                  <pre className="text-xs overflow-x-auto">
                    {JSON.stringify(tokenFlow.agent_tax_optimizer.token_exchange.response, null, 2)}
                  </pre>
                </div>
              </div>
              
              <div>
                <p className="text-xs text-purple-500 mb-1">Decoded Received Token:</p>
                <div className="bg-white p-3 rounded-md border border-purple-200">
                  <pre className="text-xs overflow-x-auto">
                    {JSON.stringify(tokenFlow.agent_tax_optimizer.token_exchange.decoded_token || {}, null, 2)}
                  </pre>
                </div>
              </div>
              
              <div>
                <p className="text-xs text-purple-500 mb-1">Calculation Response:</p>
                <div className="bg-white p-3 rounded-md border border-purple-200">
                  <pre className="text-xs overflow-x-auto">
                    {JSON.stringify(tokenFlow.agent_tax_optimizer.calculator_response.tax_result, null, 2)}
                  </pre>
                </div>
              </div>
            </div>
          </div>

          {/* Final Response Section */}
          <div className="border border-gray-200 rounded-lg p-4 bg-gray-50">
            <h4 className="text-lg font-semibold text-gray-800 mb-3">5. Final Response</h4>
            <p className="text-sm text-gray-600 mb-3">Tax Optimizer's final response with optimization results</p>
            
            <div className="bg-white p-3 rounded-md border border-gray-200">
              <pre className="text-xs overflow-x-auto">
                {JSON.stringify(tokenFlow.agent_tax_optimizer.response, null, 2)}
              </pre>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

const FinancialResultsView: React.FC<{ optimizationResult: any }> = ({ optimizationResult }) => {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="space-y-6">
      {/* Estimated Savings Card */}
      <div className="bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200 rounded-lg p-6">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-green-800">Estimated Annual Savings</h3>
            <p className="text-sm text-green-600 mt-1">Based on your financial profile</p>
          </div>
          <div className="text-right">
            <div className="text-3xl font-bold text-green-800">
              ${optimizationResult.estimated_savings.toLocaleString()}
            </div>
            <div className="text-sm text-green-600">per year</div>
          </div>
        </div>
      </div>

      {/* Financial Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <h4 className="text-sm font-medium text-gray-500">Monthly Savings</h4>
          <p className="text-2xl font-bold text-blue-600">
            ${optimizationResult.monthly_savings_potential?.toLocaleString() || '0'}
          </p>
        </div>
        
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <h4 className="text-sm font-medium text-gray-500">Current Tax Rate</h4>
          <p className="text-2xl font-bold text-red-600">
            {((optimizationResult.effective_tax_rate || 0) * 100).toFixed(1)}%
          </p>
        </div>
        
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <h4 className="text-sm font-medium text-gray-500">Tax Burden</h4>
          <p className="text-2xl font-bold text-red-600">
            ${optimizationResult.current_tax_burden?.toLocaleString() || '0'}
          </p>
        </div>
        
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <h4 className="text-sm font-medium text-gray-500">20-Year Impact</h4>
          <p className="text-2xl font-bold text-green-600">
            ${optimizationResult.retirement_impact?.toLocaleString() || '0'}
          </p>
        </div>
      </div>

      {/* Additional Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <h4 className="text-sm font-medium text-gray-500">Optimization Confidence</h4>
          <p className="text-2xl font-bold text-purple-600">
            {(optimizationResult.optimization_confidence || 0).toFixed(0)}%
          </p>
        </div>
        
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <h4 className="text-sm font-medium text-gray-500">Time to Implement</h4>
          <p className="text-2xl font-bold text-orange-600">
            {optimizationResult.time_to_implement || 0} months
          </p>
        </div>
        
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <h4 className="text-sm font-medium text-gray-500">Priority Score</h4>
          <p className="text-2xl font-bold text-indigo-600">
            {(optimizationResult.priority_score || 0).toFixed(0)}%
          </p>
        </div>
      </div>

      {/* Financial Summary Card */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-blue-800 mb-4">Your Financial Summary</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-blue-600">Annual Income</p>
            <p className="text-lg font-semibold text-blue-800">
              ${(optimizationResult.financial_summary?.annual_income || 75000).toLocaleString()}
            </p>
          </div>
          <div>
            <p className="text-sm text-blue-600">Annual Expenses</p>
            <p className="text-lg font-semibold text-blue-800">
              ${(optimizationResult.financial_summary?.annual_expenses || 45000).toLocaleString()}
            </p>
          </div>
          <div>
            <p className="text-sm text-blue-600">Current Savings</p>
            <p className="text-lg font-semibold text-blue-800">
              ${(optimizationResult.financial_summary?.current_savings || 15000).toLocaleString()}
            </p>
          </div>
          <div>
            <p className="text-sm text-blue-600">Current Investments</p>
            <p className="text-lg font-semibold text-blue-800">
              ${(optimizationResult.financial_summary?.current_investments || 25000).toLocaleString()}
            </p>
          </div>
        </div>
        <div className="mt-4 pt-4 border-t border-blue-200">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <p className="text-sm text-blue-600">Savings Rate</p>
              <p className="text-lg font-semibold text-blue-800">
                {(optimizationResult.financial_summary?.savings_rate || 40.0).toFixed(1)}%
              </p>
            </div>
            <div>
              <p className="text-sm text-blue-600">Tax Efficiency</p>
              <p className="text-lg font-semibold text-blue-800">
                {(optimizationResult.financial_summary?.tax_efficiency_score || 75).toFixed(0)}%
              </p>
            </div>
            <div>
              <p className="text-sm text-blue-600">Investment Diversification</p>
              <p className="text-lg font-semibold text-blue-800">
                {(optimizationResult.financial_summary?.investment_diversification || 65).toFixed(0)}%
              </p>
            </div>
            <div>
              <p className="text-sm text-blue-600">Emergency Fund Coverage</p>
              <p className="text-lg font-semibold text-blue-800">
                {(optimizationResult.financial_summary?.emergency_fund_coverage || 4.0).toFixed(1)} months
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Debug Section */}
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <button
          onClick={() => setExpanded(!expanded)}
          className="flex items-center text-sm font-medium text-yellow-800 hover:text-yellow-700 mb-2"
        >
          <span>{expanded ? '▼' : '▶'} Debug - Optimization Result Data</span>
        </button>
        
        {expanded && (
          <pre className="text-xs overflow-x-auto">
            {JSON.stringify(optimizationResult, null, 2)}
          </pre>
        )}
      </div>

      {/* Recommendations Card */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Tax Optimization Recommendations</h3>
        <div className="space-y-3">
          {optimizationResult.recommendations.map((rec: string, index: number) => (
            <div key={index} className="flex items-start space-x-3">
              <div className="flex-shrink-0 w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center">
                <span className="text-blue-600 text-sm font-medium">{index + 1}</span>
              </div>
              <p className="text-gray-700">{rec}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Summary Card */}
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-2">How This Works</h3>
        <p className="text-gray-700">
          Your financial plan has been optimized using AI agents with secure token-based authentication. 
          The recommendations above are based on your income, expenses, and current financial situation.
          The estimated savings represent potential tax optimization opportunities and improved financial strategies.
        </p>
      </div>
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
          {/* Financial Results Section */}
          <div className="bg-white shadow sm:rounded-lg">
            <div className="px-4 py-5 sm:p-6">
              <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                Your Financial Plan
              </h3>
              
              {planningResult.optimization_result && (
                <FinancialResultsView optimizationResult={planningResult.optimization_result} />
              )}
            </div>
          </div>

          {/* Technical Details Section */}
          <div className="bg-white shadow sm:rounded-lg">
            <div className="px-4 py-5 sm:p-6">
              <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                Technical Information
              </h3>
              <p className="text-sm text-gray-600 mb-4">
                This section shows the secure token exchange flow that powers your financial plan generation.
              </p>
              
              {planningResult.token_flow && (
                <TokenFlowView tokenFlow={planningResult.token_flow} />
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default FinancialPlanning; 