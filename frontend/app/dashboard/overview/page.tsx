"use client";

import { useEffect, useMemo, useState } from "react";
import { useAuthStore } from "@/app/store/auth-store";
import { getWorkflows, listExecutions } from "@/app/services/api";

export default function OverviewPage() {
  const token = useAuthStore((s) => s.token);
  const [workflows, setWorkflows] = useState<any[]>([]);
  const [executions, setExecutions] = useState<any[]>([]);

  const tokenSafe = useMemo(() => token, [token]);

  useEffect(() => {
    if (!tokenSafe) return;
    let cancelled = false;

    async function load() {
      const [w, e] = await Promise.all([getWorkflows(tokenSafe!), listExecutions(tokenSafe!, 8)]);
      if (!cancelled) {
        setWorkflows(w);
        setExecutions(e);
      }
    }

    load().catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [tokenSafe]);

  return (
    <div className="space-y-5">
      <div className="p-5 rounded-2xl border border-white/10 bg-white/5 shadow-glow bg-ai-gradient">
        <div className="text-xs uppercase tracking-widest text-slate-300">Overview</div>
        <div className="text-3xl font-semibold mt-2">Welcome back</div>
        <div className="text-slate-300 mt-2">Monitor workflows, run executions, and improve agent performance.</div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
          <div className="text-slate-300 text-sm">Workflows</div>
          <div className="text-2xl font-semibold mt-2">{workflows.length}</div>
        </div>
        <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
          <div className="text-slate-300 text-sm">Recent Executions</div>
          <div className="text-2xl font-semibold mt-2">{executions.length}</div>
        </div>
        <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
          <div className="text-slate-300 text-sm">Success Rate</div>
          <div className="text-2xl font-semibold mt-2">
            {executions.length ? `${Math.round((executions.filter((x) => x.status === "succeeded").length / executions.length) * 100)}%` : "—"}
          </div>
        </div>
      </div>

      <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
        <div className="flex items-center justify-between">
          <div className="font-semibold">Execution Logs</div>
          <a href="/dashboard/executions" className="text-indigo-300 text-sm hover:underline">
            View all
          </a>
        </div>
        <div className="mt-4 space-y-2">
          {executions.slice(0, 6).map((e) => (
            <div key={e.id} className="flex items-center justify-between text-sm border border-white/10 rounded-xl p-3">
              <div className="text-slate-200">
                <div className="font-medium">#{e.id.slice(0, 8)}</div>
                <div className="text-slate-400">{new Date(e.created_at).toLocaleString()}</div>
              </div>
              <div className="text-right">
                <div
                  className={[
                    "px-3 py-1 rounded-full text-xs font-medium",
                    e.status === "succeeded"
                      ? "bg-emerald-500/15 text-emerald-200 border border-emerald-500/30"
                      : e.status === "failed"
                        ? "bg-rose-500/15 text-rose-200 border border-rose-500/30"
                        : "bg-sky-500/15 text-sky-200 border border-sky-500/30",
                  ].join(" ")}
                >
                  {e.status}
                </div>
              </div>
            </div>
          ))}
          {!executions.length ? <div className="text-slate-400 text-sm">No executions yet.</div> : null}
        </div>
      </div>
    </div>
  );
}

