import { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Outlet } from 'react-router-dom';
import { MotionConfig } from 'framer-motion';
import { ProtectedRoute } from './components/layout/ProtectedRoute';

// Pages
import LandingPage from './pages/LandingPage';
import LoginPage from './pages/LoginPage';
import SignupPage from './pages/SignupPage';
import DashboardPage from './pages/DashboardPage';
import ProjectsPage from './pages/ProjectsPage';
import ProjectDetailPage from './pages/ProjectDetailPage';
import HistoryPage from './pages/HistoryPage';
import SettingsPage from './pages/SettingsPage';
import ApiDocsPage from './pages/ApiDocsPage';

import { TopNav } from './components/layout/TopNav';
import { SystemStatusRail } from './components/layout/SystemStatusRail';

function DashboardLayout() {
  useEffect(() => {
    const handlePlay = (e) => {
      if (e.target.tagName === 'VIDEO') {
        const videos = document.querySelectorAll('video');
        videos.forEach((vid) => {
          if (vid !== e.target && !vid.paused) {
            vid.pause();
            vid.currentTime = 0; // Reset as requested
          }
        });
      }
    };
    
    // Capture phase listener for 'play' since media events don't bubble
    document.addEventListener('play', handlePlay, true);
    return () => document.removeEventListener('play', handlePlay, true);
  }, []);

  return (
    <ProtectedRoute>
      <div className="min-h-screen flex flex-col bg-[#F8FAFC] text-[#0F172A] selection:bg-[#0EA5E9]/20 overflow-hidden">
        <TopNav />
        <main className="flex-1 overflow-y-auto w-full">
          <div className="mx-auto px-8 py-8 w-full max-w-[1600px]">
            <SystemStatusRail />
            <Outlet />
          </div>
        </main>
      </div>
    </ProtectedRoute>
  );
}

export default function App() {
  return (
    <MotionConfig reducedMotion="user">
      <BrowserRouter>
        <Routes>
          {/* Public */}
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/signup" element={<SignupPage />} />
          <Route path="/api-docs" element={<ApiDocsPage />} />

          {/* Authenticated Dashboard */}
          <Route path="/dashboard" element={<DashboardLayout />}>
            <Route index element={<DashboardPage />} />
            <Route path="projects" element={<ProjectsPage />} />
            <Route path="projects/:id" element={<ProjectDetailPage />} />
            <Route path="history" element={<HistoryPage />} />
            <Route path="settings" element={<SettingsPage />} />
            <Route path="api-docs" element={<ApiDocsPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </MotionConfig>
  );
}
