"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/app/store/auth-store";

export function RequireAuth({ children }: { children: React.ReactNode }) {
  const token = useAuthStore((s) => s.token);
  const router = useRouter();
  const [checked, setChecked] = useState(false);

  useEffect(() => {
    if (!token) router.replace("/login");
    setChecked(true);
  }, [token, router]);

  if (!checked) return <div className="p-6 text-slate-300">Loading…</div>;
  if (!token) return null;
  return <>{children}</>;
}

