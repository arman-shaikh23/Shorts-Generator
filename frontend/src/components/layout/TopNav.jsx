import { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Play, LogOut, Plus, PlayCircle } from 'lucide-react';
import { cn } from '../../lib/utils';
import { useAuth } from '../../hooks/useAuth';
import HowItWorksModal from '../HowItWorksModal';
import { apiFetch } from '../../api/client';

export function TopNav() {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [showHowItWorks, setShowHowItWorks] = useState(false);

  const navItems = [
    { to: '/dashboard', label: 'Dashboard' },
    { to: '/dashboard/projects', label: 'Projects' },
    { to: '/dashboard/history', label: 'History' },
    // { to: '/dashboard/templates', label: 'Templates' },
    // { to: '/dashboard/assets', label: 'AI Assets' },
    // { to: '/dashboard/pricing', label: 'Pricing' },
  ];

  const handleCreateProject = async () => {
    try {
      const res = await apiFetch('/projects', {
        method: 'POST',
        body: JSON.stringify({ title: 'Untitled Reel' }),
      });
      if (res.ok) {
        const project = await res.json();
        navigate(`/dashboard/projects/${project._id}`);
      }
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <header className="sticky top-0 z-50 w-full border-b border-[#E2E8F0] bg-white/85 shadow-[0_8px_24px_rgba(15,23,42,0.05)] backdrop-blur-xl">
      <div className="mx-auto flex h-[76px] w-full max-w-[1600px] items-center px-4 md:px-8">
        {/* Left: Logo */}
        <Link to="/dashboard" className="mr-8 flex shrink-0 items-center gap-3 rounded-xl px-1 py-1">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-aurora shadow-lg shadow-[#0EA5E9]/20">
            <Play size={18} fill="white" className="ml-0.5 text-white" />
          </div>
          <span className="text-2xl font-bold tracking-tight text-[#0F172A]">ReelForge</span>
        </Link>

        {/* Center: Navigation Links */}
        <nav className="flex flex-1 items-center gap-2 md:gap-3">
          {navItems.map((item) => {
            const isActive = location.pathname === item.to || (item.to !== '/dashboard' && location.pathname.startsWith(item.to));
            return (
              <Link
                key={item.to}
                to={item.to}
                aria-current={isActive ? 'page' : undefined}
                className={cn(
                  'rounded-xl px-3 py-2 text-sm font-semibold transition-colors',
                  isActive
                    ? 'bg-[#EFF6FF] text-[#0369A1] shadow-[inset_0_0_0_1px_rgba(14,165,233,0.18)]'
                    : 'text-[#64748B] hover:bg-[#F8FAFC] hover:text-[#0EA5E9]'
                )}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>

        {/* Right: Actions */}
        <div className="flex shrink-0 items-center gap-4">
        {/* <button className="text-[#64748B] hover:text-[#0F172A] transition">
          <Search size={20} />
        </button> */}
        {/* <button className="text-[#64748B] hover:text-[#0F172A] transition relative">
          <Bell size={20} />
          <span className="absolute top-0 right-0 w-2 h-2 bg-red-500 rounded-full border-2 border-white"></span>
        </button> */}
        
          <div className="mx-1 h-6 w-px bg-[#E2E8F0]" />
        
          {/* How It Works Button */}
          <button
            onClick={() => setShowHowItWorks(true)}
            className="inline-flex items-center gap-1.5 rounded-xl px-2 py-2 text-sm font-semibold text-[#64748B] transition hover:bg-[#F8FAFC] hover:text-[#0EA5E9]"
          >
            <PlayCircle size={16} className="text-[#0EA5E9]" />
            How It Works
          </button>

          <div className="mx-1 h-6 w-px bg-[#E2E8F0]" />

          {/* Profile Dropdown (Simplified) */}
          <div className="flex cursor-pointer items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-gradient-aurora text-xs font-bold text-white shadow-md">
              {user?.name?.charAt(0)?.toUpperCase() || 'U'}
            </div>
          </div>

          <button
            onClick={logout}
            className="rounded-lg p-1 text-[#64748B] transition hover:text-red-500"
            title="Log out"
            aria-label="Log out"
          >
            <LogOut size={18} />
          </button>

          <button
            onClick={handleCreateProject}
            className="ml-1 inline-flex items-center gap-2 rounded-xl bg-gradient-aurora px-5 py-2.5 text-sm font-bold text-white shadow-lg shadow-[#0EA5E9]/20 transition hover:-translate-y-0.5 active:translate-y-0"
          >
            <Plus size={16} /> Create Reel
          </button>
        </div>
      </div>

      <HowItWorksModal 
        isOpen={showHowItWorks} 
        onClose={() => setShowHowItWorks(false)} 
      />
    </header>
  );
}
