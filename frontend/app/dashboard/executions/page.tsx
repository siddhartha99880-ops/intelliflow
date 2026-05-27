"use client";

import { useEffect, useState } from "react";
import { useAuthStore } from "@/app/store/auth-store";
import { listExecutions } from "@/app/services/api";
import { Card } from "@/app/components/ui/card";

export default function ExecutionsPage() {
  const token = useAuthStore((s) => s.token);
  const [executions, setExecutions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    setLoading(true);
    listExecutions(token, 30)
      .then((res) => {
        if (!cancelled) setExecutions(res);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [token]);

  return (
    <div className="space-y-4">
      <div className="p-5 rounded-2xl border border-white/10 bg-white/5 shadow-glow bg-ai-gradient">
        <div className="text-xs uppercase tracking-widest text-slate-300">Execution Logs</div>
        <div className="text-2xl font-semibold mt-2">Everything the agents did</div>
      </div>

      <Card className="p-4">
        {loading ? (
          <div className="text-slate-300 text-sm">Loading…</div>
        ) : !executions.length ? (
          <div className="text-slate-400 text-sm">No executions yet.</div>
        ) : (
          <div className="space-y-2">
            {executions.map((e) => (
              <div key={e.id} className="flex items-center justify-between rounded-xl border border-white/10 p-3">
                <div>
                  <div className="font-medium">#{e.id.slice(0, 8)} · {e.workflow_id}</div>
                  <div className="text-slate-400 text-xs">{new Date(e.created_at).toLocaleString()}</div>
                </div>
                <div className="text-right">
                  <div className="text-sm">{e.status}</div>
                  {typeof e.duration_ms === "number" ? <div className="text-slate-400 text-xs">{e.duration_ms} ms</div> : null}
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}

