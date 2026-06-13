import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';

export function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-[#F8FAFC] flex items-center justify-center">
        <div className="flex flex-col items-center gap-6">
          <div className="relative w-16 h-16">
            <div className="absolute inset-0 border-4 border-[#0EA5E9]/20 rounded-2xl animate-pulse"></div>
            <div className="absolute inset-0 border-4 border-[#0EA5E9] rounded-2xl border-t-transparent animate-spin"></div>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-2xl font-black tracking-tight text-[#0F172A]">ReelForge</span>
            <span className="text-[#0EA5E9] font-black text-2xl animate-pulse">.</span>
          </div>
        </div>
      </div>
    );
  }

  // Enforce authentication
  if (!user) return <Navigate to="/login" replace />;

  return children;
}
