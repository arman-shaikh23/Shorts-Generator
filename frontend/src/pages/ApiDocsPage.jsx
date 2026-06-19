import { ExternalLink } from 'lucide-react';
import { toApiUrl } from '../api/client';

export default function ApiDocsPage() {
  const docsUrl = toApiUrl('/docs');
  const openapiUrl = toApiUrl('/openapi.json');

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden min-h-screen">
      <div className="p-6 border-b border-slate-100 bg-slate-50">
        <h1 className="text-2xl font-semibold text-slate-800">API Documentation</h1>
        <p className="text-slate-500 mt-1">
          Interactive API reference served by the backend.
        </p>
        <div className="mt-4 flex flex-wrap gap-3">
          <a
            href={docsUrl}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-slate-900 text-white text-sm font-medium hover:bg-slate-700 transition"
          >
            Open Swagger UI <ExternalLink size={14} />
          </a>
          <a
            href={openapiUrl}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-slate-300 text-slate-700 text-sm font-medium hover:bg-slate-100 transition"
          >
            Open OpenAPI JSON <ExternalLink size={14} />
          </a>
        </div>
      </div>
      <div className="p-6">
        <iframe
          title="API Docs"
          src={docsUrl}
          className="w-full min-h-[72vh] rounded-lg border border-slate-200"
        />
      </div>
    </div>
  );
}
