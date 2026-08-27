import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Sparkles, Loader2 } from "lucide-react";
import { useAuth } from "../context/AuthContext.jsx";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    if (!email || !password) {
      setError("Please enter your email and password.");
      return;
    }
    setLoading(true);
    try {
      await login(email, password);
      navigate("/dashboard");
    } catch (err) {
      setError(err.response?.data?.detail || "Login failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative min-h-screen flex items-center justify-center overflow-hidden bg-[#080b1d] px-4 py-8 text-white">
      <div className="home-orb home-orb-blue pointer-events-none" />
      <div className="home-orb home-orb-pink pointer-events-none" />
      <div className="relative z-10 w-full max-w-md animate-slide-up">
        <div className="flex items-center gap-2 justify-center mb-8">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-cyan-300 via-indigo-500 to-fuchsia-500 flex items-center justify-center shadow-lg shadow-indigo-500/30">
            <Sparkles size={20} className="text-white" />
          </div>
          <span className="font-semibold text-xl">DocIntel</span>
        </div>

        <div className="rounded-3xl border border-white/15 bg-white/[0.09] p-6 shadow-2xl shadow-indigo-950/40 backdrop-blur-xl sm:p-8">
          <h1 className="text-xl font-semibold mb-1">Welcome back</h1>
          <p className="text-sm text-slate-300 mb-6">Log in to access your documents.</p>

          {error && (
            <div className="mb-4 text-sm text-red-200 bg-red-400/10 border border-red-300/20 rounded-xl px-3 py-2">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-200 mb-1">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="premium-input w-full rounded-xl px-3 py-2.5"
                placeholder="you@example.com"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-200 mb-1">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="premium-input w-full rounded-xl px-3 py-2.5"
                placeholder="••••••••"
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="premium-button w-full flex items-center justify-center gap-2 font-medium py-2.5 rounded-xl"
            >
              {loading && <Loader2 size={16} className="animate-spin" />}
              {loading ? "Logging in..." : "Log in"}
            </button>
          </form>

          <p className="text-sm text-slate-300 mt-6 text-center">
            Don't have an account?{" "}
            <Link to="/register" className="text-brand-600 font-medium hover:underline">
              Register
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
