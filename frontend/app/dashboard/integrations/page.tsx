"use client";

import { useEffect, useState } from "react";
import { Card } from "@/app/components/ui/card";

export default function IntegrationsPage() {
  const [status, setStatus] = useState<any>(null);

  useEffect(() => {
    async function load() {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/integrations/health`);
      setStatus(await res.json());
    }
    load().catch(() => {});
  }, []);

  return (
    <div className="space-y-4">
      <Card className="p-5">
        <div className="text-xs uppercase tracking-widest text-slate-300">Integrations</div>
        <div className="text-2xl font-semibold mt-2">Connect your business stack</div>
        <div className="text-slate-300 text-sm mt-2">Slack, Notion, Google Workspace and mock ERP are available for workflow nodes.</div>
      </Card>

      <Card className="p-5">
        <div className="text-sm font-semibold">Status</div>
        <pre className="mt-3 text-xs text-slate-300 whitespace-pre-wrap">{status ? JSON.stringify(status, null, 2) : "Loading…"}</pre>
      </Card>
    </div>
  );
}

