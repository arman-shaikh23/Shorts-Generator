import React from 'react';
import SwaggerUI from 'swagger-ui-react';
import 'swagger-ui-react/swagger-ui.css';

const ApiDocsPage = () => {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden min-h-screen">
      <div className="p-6 border-b border-slate-100 bg-slate-50">
        <h1 className="text-2xl font-semibold text-slate-800">API Documentation</h1>
        <p className="text-slate-500 mt-1">Interactive API reference powered by Swagger UI</p>
      </div>
      <div className="swagger-wrapper">
        <SwaggerUI url="http://localhost:8000/openapi.json" />
      </div>
    </div>
  );
};

export default ApiDocsPage;
