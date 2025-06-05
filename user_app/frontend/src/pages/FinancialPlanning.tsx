import React, { useState } from 'react';
import { useQuery, useMutation } from 'react-query';
import axios from 'axios';

interface FinancialData {
  income: number;
  expenses: number;
  savings: number;
  investments: number;
}

interface PlanningResult {
  recommendations: string[];
  taxOptimization: any;
  riskAssessment: any;
}

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
      const response = await axios.post('/api/financial-planning', financialData);
      return response.data;
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
    refetchPlanning();
  };

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
        <>
          <div className="bg-white shadow sm:rounded-lg">
            <div className="px-4 py-5 sm:p-6">
              <h3 className="text-lg leading-6 font-medium text-gray-900">
                Recommendations
              </h3>
              <div className="mt-4">
                <ul className="list-disc pl-5 space-y-2">
                  {planningResult.recommendations.map((rec, index) => (
                    <li key={index} className="text-sm text-gray-500">
                      {rec}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>

          <div className="bg-white shadow sm:rounded-lg">
            <div className="px-4 py-5 sm:p-6">
              <h3 className="text-lg leading-6 font-medium text-gray-900">
                Tax Optimization
              </h3>
              <div className="mt-4">
                <pre className="bg-gray-50 p-4 rounded-md overflow-x-auto">
                  {JSON.stringify(planningResult.taxOptimization, null, 2)}
                </pre>
              </div>
            </div>
          </div>

          <div className="bg-white shadow sm:rounded-lg">
            <div className="px-4 py-5 sm:p-6">
              <h3 className="text-lg leading-6 font-medium text-gray-900">
                Risk Assessment
              </h3>
              <div className="mt-4">
                <pre className="bg-gray-50 p-4 rounded-md overflow-x-auto">
                  {JSON.stringify(planningResult.riskAssessment, null, 2)}
                </pre>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default FinancialPlanning; 