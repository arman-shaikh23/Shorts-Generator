import React from 'react';
import { motion } from 'framer-motion';
import { LogOut, User, Shield, CreditCard, Paintbrush } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { Button } from '../components/ui/Button';

export default function SettingsPage() {
  const { user, logout } = useAuth();

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="max-w-[800px]">
      <div className="mb-10">
        <h1 className="text-3xl font-bold tracking-tight mb-1">Settings</h1>
        <p className="text-gray-500">Manage your account preferences and billing.</p>
      </div>

      <div className="flex flex-col md:flex-row gap-8">
        
        {/* Settings Nav (Visual Only) */}
        <div className="w-full md:w-64 flex flex-col gap-1">
          <button className="flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium bg-white/10 text-white">
            <User size={16} /> Account
          </button>
          <button className="flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium text-gray-400 hover:text-white hover:bg-white/[0.03] transition">
            <Shield size={16} /> Security
          </button>
          <button className="flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium text-gray-400 hover:text-white hover:bg-white/[0.03] transition">
            <Paintbrush size={16} /> Brand Kit
          </button>
          <button className="flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium text-gray-400 hover:text-white hover:bg-white/[0.03] transition">
            <CreditCard size={16} /> Billing
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 space-y-8">
          
          {/* Profile Section */}
          <section className="bg-[#111] border border-white/10 rounded-2xl p-7">
            <h2 className="text-lg font-semibold mb-5 border-b border-white/10 pb-4">Profile Details</h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-gray-400 mb-2">Full Name</label>
                <input
                  type="text"
                  defaultValue={user?.name}
                  disabled
                  className="w-full bg-white/[0.03] border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-blue-500/50 transition text-sm opacity-60 cursor-not-allowed"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-2">Email Address</label>
                <input
                  type="email"
                  defaultValue={user?.email}
                  disabled
                  className="w-full bg-white/[0.03] border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-blue-500/50 transition text-sm opacity-60 cursor-not-allowed"
                />
              </div>
            </div>
            <p className="text-xs text-gray-500 mt-4">Profile editing is currently disabled in this version.</p>
          </section>

          {/* Danger Zone */}
          <section className="bg-red-500/5 border border-red-500/20 rounded-2xl p-7">
            <h2 className="text-lg font-semibold mb-2 text-red-400">Danger Zone</h2>
            <p className="text-sm text-red-400/70 mb-5">Sign out of your account on this device.</p>
            <Button variant="danger" size="md" onClick={logout}>
              <LogOut size={16} className="mr-2" />
              Sign Out
            </Button>
          </section>

        </div>
      </div>
    </motion.div>
  );
}
