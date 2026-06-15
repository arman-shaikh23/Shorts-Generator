import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Play, Bell, Search, LayoutDashboard, FolderKanban, Sparkles, LogOut, Plus } from 'lucide-react';
import { cn } from '../../lib/utils';
import { useAuth } from '../../hooks/useAuth';

export function TopNav() {
  const { user, logout } = useAuth();
  const location = useLocation();

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
      const res = await fetch('http://localhost:8000/api/v1/projects', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
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
    <header className="sticky top-0 z-50 h-[80px] w-full bg-white/80 backdrop-blur-[20px] border-b border-[#E2E8F0] shadow-sm flex items-center px-8">
      {/* Left: Logo */}
      <Link to="/dashboard" className="flex items-center gap-3 shrink-0 mr-12">
        <div className="w-10 h-10 rounded-xl bg-gradient-aurora flex items-center justify-center shadow-lg shadow-[#0EA5E9]/20">
          <Play size={18} fill="white" className="ml-0.5 text-white" />
        </div>
        <span className="text-2xl font-bold tracking-tight text-[#0F172A]">ReelForge</span>
      </Link>

      {/* Center: Navigation Links */}
      <nav className="flex items-center gap-8 flex-1">
        {navItems.map((item) => {
          const isActive = location.pathname === item.to || (item.to !== '/dashboard' && location.pathname.startsWith(item.to));
          return (
            <Link
              key={item.to}
              to={item.to}
              className={cn(
                'text-sm font-medium transition-colors relative py-2',
                isActive ? 'text-[#0F172A]' : 'text-[#64748B] hover:text-[#0EA5E9]'
              )}
            >
              {item.label}
              {isActive && (
                <span className="absolute bottom-[-1px] left-0 w-full h-[2px] bg-[#0EA5E9] rounded-t-full" />
              )}
            </Link>
          );
        })}
      </nav>

      {/* Right: Actions */}
      <div className="flex items-center gap-5 shrink-0">
        {/* <button className="text-[#64748B] hover:text-[#0F172A] transition">
          <Search size={20} />
        </button> */}
        {/* <button className="text-[#64748B] hover:text-[#0F172A] transition relative">
          <Bell size={20} />
          <span className="absolute top-0 right-0 w-2 h-2 bg-red-500 rounded-full border-2 border-white"></span>
        </button> */}
        
        <div className="w-px h-6 bg-[#E2E8F0] mx-1"></div>
        
        {/* Profile Dropdown (Simplified) */}
        <div className="flex items-center gap-3 cursor-pointer group">
          <div className="w-9 h-9 rounded-full bg-gradient-aurora text-white flex items-center justify-center text-xs font-bold shadow-md">
            {user?.name?.charAt(0)?.toUpperCase() || 'U'}
          </div>
        </div>

        <button onClick={logout} className="text-[#64748B] hover:text-red-500 transition" title="Log out">
          <LogOut size={18} />
        </button>

        <button onClick={handleCreateProject} className="ml-2 bg-gradient-aurora text-white px-5 py-2.5 rounded-xl text-sm font-bold shadow-lg shadow-[#0EA5E9]/20 hover:scale-105 transition-transform active:scale-95 flex items-center gap-2">
          <Plus size={16} /> Create Reel
        </button>
      </div>
    </header>
  );
}
