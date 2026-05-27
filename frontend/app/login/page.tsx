"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { login } from "@/app/services/api";
import { useAuthStore } from "@/app/store/auth-store";

export default function LoginPage() {
  const router = useRouter();
  const setToken = useAuthStore((s) => s.setToken);

  const [email, setEmail] = useState("demo@intelliflow.local");
  const [password, setPassword] = useState("demo-password");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await login(email, password);
      setToken(res.access_token);
      router.replace("/dashboard/overview");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-ai-gradient">
      <div className="w-full max-w-md p-6 rounded-2xl border border-white/10 bg-white/5 shadow-glow">
        <div className="mb-6">
          <div className="text-2xl font-semibold">IntelliFlow</div>
          <div className="text-slate-300 text-sm mt-1">AI workflow automation</div>
        </div>

        <form onSubmit={onSubmit} className="space-y-3">
          <div>
            <label className="text-sm text-slate-300">Email</label>
            <input
              className="mt-1 w-full rounded-xl border border-white/10 bg-black/20 px-3 py-2 outline-none"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>
          <div>
            <label className="text-sm text-slate-300">Password</label>
            <input
              type="password"
              className="mt-1 w-full rounded-xl border border-white/10 bg-black/20 px-3 py-2 outline-none"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>

          {error ? <div className="text-sm text-red-300">{error}</div> : null}

          <button
            disabled={loading}
            className="w-full rounded-xl bg-indigo-600 hover:bg-indigo-500 px-4 py-2 font-medium disabled:opacity-60"
          >
            {loading ? "Signing in..." : "Sign in"}
          </button>
        </form>
      </div>
    </div>
  );
}

