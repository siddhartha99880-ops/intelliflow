import { RequireAuth } from "@/app/components/auth/RequireAuth";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <RequireAuth>
      <div className="min-h-screen">
        <div className="hidden md:flex md:fixed md:inset-y-0 md:w-72">
          <aside className="w-72 border-r border-white/10 bg-slate-950/50 backdrop-blur-xl">
            <div className="p-5 font-semibold text-white">IntelliFlow</div>
            <nav className="px-4 pb-6 space-y-2">
              {[
                ["overview", "Overview"],
                ["builder", "Workflow Builder"],
                ["agents", "Agents"],
                ["integrations", "Integrations"],
                ["executions", "Execution Logs"],
                ["analytics", "Analytics"],
                ["settings", "Settings"],
              ].map(([slug, label]) => (
                <a
                  key={slug}
                  href={`/dashboard/${slug}`}
                  className="block px-3 py-2 rounded-xl hover:bg-white/5 border border-transparent hover:border-white/10 text-slate-200"
                >
                  {label}
                </a>
              ))}
            </nav>
          </aside>
        </div>

        <div className="md:pl-72">
          <header className="p-6 border-b border-white/10 bg-slate-950/40 backdrop-blur-xl sticky top-0 z-10">
            <div className="max-w-6xl mx-auto">
              <div className="text-sm text-slate-300">AI workflow automation</div>
              <div className="text-2xl font-semibold mt-1">Workspace</div>
            </div>
          </header>
          <main className="p-6">
            <div className="max-w-6xl mx-auto">{children}</div>
          </main>
        </div>
      </div>
    </RequireAuth>
  );
}

