import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Play } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';

export default function SignupPage() {
  const { signup } = useAuth();
  const navigate = useNavigate();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    if (password.length < 6) {
      setError('Password must be at least 6 characters.');
      return;
    }
    setLoading(true);
    try {
      await signup(name, email, password);
      navigate('/dashboard');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#F8FAFC] text-[#0F172A] relative px-6 overflow-hidden selection:bg-[#0EA5E9]/20">
      
      {/* Abstract Aurora Background */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-[10%] right-[15%] w-[40%] h-[50%] bg-[#14B8A6]/10 blur-[120px] rounded-full mix-blend-multiply" />
        <div className="absolute bottom-[10%] left-[10%] w-[35%] h-[45%] bg-[#0EA5E9]/10 blur-[120px] rounded-full mix-blend-multiply" />
      </div>

      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="w-full max-w-md relative z-10 my-12">
        
        {/* Logo */}
        <Link to="/" className="flex items-center gap-3 justify-center mb-10 group">
          <div className="w-12 h-12 rounded-2xl bg-gradient-aurora flex items-center justify-center shadow-lg shadow-[#0EA5E9]/20 group-hover:scale-105 transition-transform">
            <Play size={20} fill="white" className="ml-0.5 text-white" />
          </div>
          <span className="text-3xl font-extrabold tracking-tight">ReelForge</span>
        </Link>

        {/* Card */}
        <div className="p-10 rounded-[2rem] bg-white border border-[#E2E8F0] shadow-[0_30px_60px_rgba(0,0,0,0.05)] relative overflow-hidden">
          <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-aurora"></div>
          
          <h2 className="text-3xl font-black mb-2 text-[#0F172A] tracking-tight">Create your account</h2>
          <p className="text-[#64748B] font-medium mb-8">Start generating cinematic property reels.</p>

          {error && (
            <div className="bg-red-50 border border-red-100 text-red-600 px-5 py-4 rounded-2xl text-sm font-medium mb-8">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-sm font-bold text-[#0F172A] mb-2">Full Name</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="John Doe"
                required
                className="w-full bg-[#F8FAFC] border border-[#E2E8F0] rounded-2xl px-5 py-4 text-[#0F172A] placeholder:text-[#94a3b8] font-medium focus:outline-none focus:border-[#0EA5E9] focus:ring-4 focus:ring-[#0EA5E9]/10 transition-all"
              />
            </div>
            <div>
              <label className="block text-sm font-bold text-[#0F172A] mb-2">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@company.com"
                required
                className="w-full bg-[#F8FAFC] border border-[#E2E8F0] rounded-2xl px-5 py-4 text-[#0F172A] placeholder:text-[#94a3b8] font-medium focus:outline-none focus:border-[#0EA5E9] focus:ring-4 focus:ring-[#0EA5E9]/10 transition-all"
              />
            </div>
            <div>
              <label className="block text-sm font-bold text-[#0F172A] mb-2">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Min. 6 characters"
                required
                className="w-full bg-[#F8FAFC] border border-[#E2E8F0] rounded-2xl px-5 py-4 text-[#0F172A] placeholder:text-[#94a3b8] font-medium focus:outline-none focus:border-[#0EA5E9] focus:ring-4 focus:ring-[#0EA5E9]/10 transition-all"
              />
            </div>

            <button 
              type="submit" 
              disabled={loading}
              className="w-full bg-[#0F172A] text-white py-4 rounded-2xl font-bold text-lg shadow-lg hover:bg-[#1e293b] hover:-translate-y-0.5 transition-all disabled:opacity-50 mt-4 flex items-center justify-center gap-2"
            >
              {loading ? 'Creating...' : 'Create Account'}
            </button>
          </form>

          <p className="text-center text-[#64748B] font-medium mt-8">
            Already have an account?{' '}
            <Link to="/login" className="text-[#0EA5E9] hover:text-[#06B6D4] transition-colors font-bold">Sign in</Link>
          </p>
        </div>
      </motion.div>
    </div>
  );
}
