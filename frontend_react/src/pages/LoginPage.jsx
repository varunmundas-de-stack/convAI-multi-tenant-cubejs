import { useState } from 'react'
import { loginUser } from '../api/client'

export default function LoginPage({ onLogin }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError]       = useState('')
  const [loading, setLoading]   = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const data = await loginUser(username, password)
      if (data.success) onLogin(data.user)
      else setError(data.error || 'Invalid credentials')
    } catch {
      setError('Network error. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4 relative overflow-hidden">

      {/* ── Animated gradient background ── */}
      <div className="absolute inset-0" style={{
        background: 'linear-gradient(135deg, #1e1b4b 0%, #312e81 20%, #4c1d95 45%, #6d28d9 70%, #7c3aed 100%)',
      }} />

      {/* Floating glow orbs */}
      <div className="absolute top-[10%] left-[15%] w-80 h-80 rounded-full opacity-30 blur-3xl animate-pulse-slow"
           style={{ background: 'radial-gradient(circle, #818cf8, transparent)' }} />
      <div className="absolute bottom-[15%] right-[10%] w-96 h-96 rounded-full opacity-25 blur-3xl animate-pulse-slow"
           style={{ background: 'radial-gradient(circle, #a855f7, transparent)', animationDelay: '2s' }} />
      <div className="absolute top-[55%] left-[60%] w-60 h-60 rounded-full opacity-20 blur-3xl animate-pulse-slow"
           style={{ background: 'radial-gradient(circle, #ec4899, transparent)', animationDelay: '4s' }} />

      {/* ── Card ── */}
      <div className="relative z-10 w-full max-w-md animate-scale-in">
        <div className="glass-dark rounded-3xl p-8 shadow-2xl border border-white/10">

          {/* Logo */}
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl mb-5 shadow-glow"
                 style={{ background: 'linear-gradient(135deg, rgba(99,102,241,0.8), rgba(168,85,247,0.8))' }}>
              <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                  d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <h1 className="text-2xl font-black text-white tracking-tight">CPG Sales Assistant</h1>
            <p className="text-white/50 text-sm mt-1.5">AI-powered analytics platform</p>
          </div>

          {/* Error */}
          {error && (
            <div className="mb-5 px-4 py-3 rounded-xl bg-red-500/20 border border-red-500/30 text-sm text-red-200 flex items-center gap-2 animate-scale-in">
              <svg className="w-4 h-4 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
              {error}
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-white/60 uppercase tracking-widest mb-2">
                Username
              </label>
              <input
                type="text"
                value={username}
                onChange={e => setUsername(e.target.value)}
                required
                autoComplete="username"
                placeholder="Enter your username"
                className="w-full px-4 py-3 rounded-xl bg-white/10 border border-white/15 text-white placeholder-white/30 text-sm focus:outline-none focus:ring-2 focus:ring-violet-400/60 focus:border-violet-400/40 focus:bg-white/15 transition-all"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-white/60 uppercase tracking-widest mb-2">
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                required
                autoComplete="current-password"
                placeholder="Enter your password"
                className="w-full px-4 py-3 rounded-xl bg-white/10 border border-white/15 text-white placeholder-white/30 text-sm focus:outline-none focus:ring-2 focus:ring-violet-400/60 focus:border-violet-400/40 focus:bg-white/15 transition-all"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3.5 mt-2 rounded-xl font-bold text-sm text-white transition-all duration-200 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed shadow-glow hover:shadow-glow hover:opacity-90"
              style={{ background: 'linear-gradient(135deg, #4f46e5, #7c3aed, #9333ea)' }}
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
                  </svg>
                  Signing in…
                </span>
              ) : 'Sign In →'}
            </button>
          </form>

        </div>

        {/* Bottom tagline */}
        <p className="text-center text-white/25 text-xs mt-4">
          Secure · Multi-tenant · Role-aware
        </p>
      </div>
    </div>
  )
}
