"use client";

import { Card } from "@/app/components/ui/card";
import { useAuthStore } from "@/app/store/auth-store";

export default function SettingsPage() {
  const token = useAuthStore((s) => s.token);

  return (
    <div className="space-y-4">
      <Card className="p-5">
        <div className="text-xs uppercase tracking-widest text-slate-300">Settings</div>
        <div className="text-2xl font-semibold mt-2">Workspace & API keys</div>
        <div className="text-slate-300 mt-2 text-sm">
          MVP: token-based sessions are stored in memory. Add invite members and API key management next.
        </div>
      </Card>

      <Card className="p-5">
        <div className="text-sm text-slate-300">Session token</div>
        <div className="mt-2 text-xs break-all text-slate-200">{token ? token.slice(0, 28) + "…" : "—"}</div>
      </Card>
    </div>
  );
}

