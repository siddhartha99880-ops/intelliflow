"use client";

import { useEffect, useMemo, useState } from "react";
import { listExecutions } from "@/app/services/api";
import { useAuthStore } from "@/app/store/auth-store";
import { Card } from "@/app/components/ui/card";
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from "recharts";

const COLORS = ["#6366f1", "#34d399", "#fb7185", "#38bdf8"];

export default function AnalyticsPage() {
  const token = useAuthStore((s) => s.token);
  const [executions, setExecutions] = useState<any[]>([]);

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    listExecutions(token, 60)
      .then((res) => {
        if (!cancelled) setExecutions(res);
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [token]);

  const stats = useMemo(() => {
    const total = executions.length || 1;
    const succeeded = executions.filter((x) => x.status === "succeeded").length;
    const failed = executions.filter((x) => x.status === "failed").length;
    const queued = executions.filter((x) => x.status === "queued").length;
    const running = executions.filter((x) => x.status === "running").length;
    const successRate = Math.round((succeeded / total) * 100);
    const times = executions.map((x) => (typeof x.duration_ms === "number" ? x.duration_ms : null)).filter((x) => x !== null) as number[];
    const avgTime = times.length ? Math.round(times.reduce((a, b) => a + b, 0) / times.length) : null;

    const byStatus = [
      { name: "succeeded", value: succeeded },
      { name: "failed", value: failed },
      { name: "running", value: running },
      { name: "queued", value: queued },
    ];
    return { succeeded, failed, queued, running, successRate, avgTime, byStatus };
  }, [executions]);

  return (
    <div className="space-y-4">
      <div className="p-5 rounded-2xl border border-white/10 bg-white/5 shadow-glow bg-ai-gradient">
        <div className="text-xs uppercase tracking-widest text-slate-300">Analytics</div>
        <div className="text-2xl font-semibold mt-2">Execution performance</div>
        <div className="text-slate-300 mt-2">
          Success rate: <span className="text-indigo-200">{stats.successRate}%</span> {stats.avgTime ? `· Avg ${stats.avgTime} ms` : ""}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card className="p-4">
          <div className="text-slate-300 text-sm">Succeeded</div>
          <div className="text-2xl font-semibold mt-2">{stats.succeeded}</div>
        </Card>
        <Card className="p-4">
          <div className="text-slate-300 text-sm">Failed</div>
          <div className="text-2xl font-semibold mt-2">{stats.failed}</div>
        </Card>
        <Card className="p-4">
          <div className="text-slate-300 text-sm">Avg Execution Time</div>
          <div className="text-2xl font-semibold mt-2">{stats.avgTime ?? "—"}</div>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card className="p-4">
          <div className="font-semibold mb-2">Status distribution</div>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={stats.byStatus} dataKey="value" nameKey="name" outerRadius={90} label>
                  {stats.byStatus.map((_, idx) => (
                    <Cell key={idx} fill={COLORS[idx % COLORS.length]} />
                  ))}
                </Pie>
              </PieChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card className="p-4">
          <div className="font-semibold mb-2">Counts by status</div>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={stats.byStatus} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis allowDecimals={false} />
                <Tooltip />
                <Bar dataKey="value" fill="#4f46e5" radius={10} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>
    </div>
  );
}

