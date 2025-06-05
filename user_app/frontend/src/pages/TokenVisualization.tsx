import React, { useEffect, useState } from 'react';
import { useQuery } from 'react-query';
import axios from 'axios';
import { jwtDecode } from 'jwt-decode';

interface TokenInfo {
  header: any;
  payload: any;
  signature: string;
}

const TokenVisualization: React.FC = () => {
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [tokenInfo, setTokenInfo] = useState<TokenInfo | null>(null);

  const { data: delegationInfo } = useQuery('delegation', async () => {
    const response = await axios.get('/api/delegation-info');
    return response.data;
  });

  useEffect(() => {
    const fetchToken = async () => {
      try {
        const response = await axios.get('/api/token');
        const token = response.data.access_token;
        setAccessToken(token);
        
        if (token) {
          const decoded = jwtDecode(token);
          setTokenInfo({
            header: JSON.parse(atob(token.split('.')[0])),
            payload: decoded,
            signature: token.split('.')[2]
          });
        }
      } catch (error) {
        console.error('Error fetching token:', error);
      }
    };

    fetchToken();
  }, []);

  return (
    <div className="space-y-6">
      <div className="bg-white shadow sm:rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900">
            Token Information
          </h3>
          
          {tokenInfo && (
            <div className="mt-4 space-y-4">
              <div>
                <h4 className="text-sm font-medium text-gray-500">Header</h4>
                <pre className="mt-1 bg-gray-50 p-4 rounded-md overflow-x-auto">
                  {JSON.stringify(tokenInfo.header, null, 2)}
                </pre>
              </div>
              
              <div>
                <h4 className="text-sm font-medium text-gray-500">Payload</h4>
                <pre className="mt-1 bg-gray-50 p-4 rounded-md overflow-x-auto">
                  {JSON.stringify(tokenInfo.payload, null, 2)}
                </pre>
              </div>
              
              <div>
                <h4 className="text-sm font-medium text-gray-500">Signature</h4>
                <pre className="mt-1 bg-gray-50 p-4 rounded-md overflow-x-auto">
                  {tokenInfo.signature}
                </pre>
              </div>
            </div>
          )}
        </div>
      </div>

      {delegationInfo && (
        <div className="bg-white shadow sm:rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900">
              Delegation Chain
            </h3>
            <div className="mt-4">
              <pre className="bg-gray-50 p-4 rounded-md overflow-x-auto">
                {JSON.stringify(delegationInfo, null, 2)}
              </pre>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TokenVisualization; 