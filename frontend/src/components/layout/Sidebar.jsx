import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, FolderKanban, PlusCircle, Clock, BarChart3, Settings, Play, LogOut } from 'lucide-react';
import { cn } from '../../lib/utils';
import { useAuth } from '../../hooks/useAuth';

const navItems = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Overview' },
  { to: '/dashboard/projects', icon: FolderKanban, label: 'Projects' },
  { to: '/dashboard/create', icon: PlusCircle, label: 'Create Reel' },
  { to: '/dashboard/history', icon: Clock, label: 'History' },
];

function SidebarLink({ to, icon: Icon, label }) {
  const location = useLocation();
  const isActive = location.pathname === to;

  return (
    <Link
      to={to}
      className={cn(
        'flex items-center gap-3 px-4 py-2.5 rounded-lg transition-all duration-200',
        isActive
          ? 'bg-[#8B5CF6]/15 text-[#8B5CF6] font-medium border border-[#8B5CF6]/20'
          : 'text-gray-400 hover:bg-white/[0.04] hover:text-gray-200 border border-transparent'
      )}
    >
      <Icon size={18} strokeWidth={isActive ? 2.2 : 1.8} />
      <span className="text-sm">{label}</span>
    </Link>
  );
}

export function Sidebar() {
  const { user, logout } = useAuth();

  return (
    <aside className="w-[280px] h-screen sticky top-0 border-r border-[#22252A] bg-transparent flex flex-col p-6 shrink-0 z-50">
      {/* Logo */}
      <Link to="/dashboard" className="flex items-center gap-3 px-2 mb-10">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#6366F1] to-[#8B5CF6] flex items-center justify-center shadow-lg shadow-[#6366F1]/20">
          <Play size={14} fill="white" className="ml-0.5" />
        </div>
        <span className="text-xl font-bold tracking-tight text-white">ReelForge<span className="text-[#8B5CF6]">.ai</span></span>
      </Link>

      {/* Main Nav */}
      <nav className="flex flex-col gap-1 flex-1">
        {navItems.map((item) => (
          <SidebarLink key={item.to} {...item} />
        ))}
      </nav>

      {/* Bottom Nav */}
      <div className="flex flex-col gap-1 mt-auto">
        <Link to="/dashboard/settings" className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium text-gray-400 hover:text-white hover:bg-white/[0.03] transition mb-4">
          <Settings size={18} />
          Settings
        </Link>

        {/* User Profile */}
        <div className="mt-3 pt-4 border-t border-white/5">
          <div className="flex items-center gap-3 px-3">
            <div className="w-9 h-9 rounded-full bg-gradient-to-br from-gray-700 to-gray-800 border border-white/10 flex items-center justify-center text-xs font-bold text-gray-300">
              {user?.name?.charAt(0)?.toUpperCase() || 'U'}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-200 truncate">{user?.name || 'Guest'}</p>
              <p className="text-xs text-gray-600 truncate">{user?.plan || 'Free'} Plan</p>
            </div>
            <button onClick={logout} className="p-2 rounded-lg text-gray-600 hover:text-red-400 hover:bg-red-400/10 transition" title="Sign out">
              <LogOut size={16} />
            </button>
          </div>
        </div>
      </div>
    </aside>
  );
}
