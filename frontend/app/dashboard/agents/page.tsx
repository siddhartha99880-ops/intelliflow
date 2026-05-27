"use client";

import { Card } from "@/app/components/ui/card";

export default function AgentsPage() {
  return (
    <div className="space-y-4">
      <Card className="p-5">
        <div className="text-xs uppercase tracking-widest text-slate-300">Agents</div>
        <div className="text-2xl font-semibold mt-2">Multi-agent orchestration</div>
        <div className="text-slate-300 mt-2 text-sm">
          Research, summarization, decisioning, email drafting, and ERP updates are available as workflow nodes.
        </div>
      </Card>
      <Card className="p-5">
        <div className="text-sm text-slate-300">
          MVP note: OpenAI calls are enabled only if `OPENAI_API_KEY` is configured in the backend. Otherwise, the system uses deterministic demo fallbacks.
        </div>
      </Card>
    </div>
  );
}

