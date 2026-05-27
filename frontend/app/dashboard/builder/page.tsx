"use client";

import { useEffect, useMemo, useState } from "react";
import ReactFlow, {
  Background,
  Controls,
  Edge,
  Node,
  addEdge,
  useEdgesState,
  useNodesState,
} from "reactflow";
import "reactflow/dist/style.css";

import { createWorkflow, executeWorkflow } from "@/app/services/api";
import { useAuthStore } from "@/app/store/auth-store";

import { Card } from "@/app/components/ui/card";
import { Button } from "@/app/components/ui/button";
import { Input } from "@/app/components/ui/input";
import { Label } from "@/app/components/ui/label";

type NodeType =
  | "trigger"
  | "llm_agent"
  | "decision"
  | "api_action"
  | "slack"
  | "notion"
  | "email"
  | "delay"
  | "human_approval";

function makeNodeId(): string {
  // ReactFlow uses string IDs. Backend expects UUIDs, so we generate UUID strings.
  return crypto.randomUUID();
}

const PALETTE: Array<{ type: NodeType; label: string }> = [
  { type: "trigger", label: "Trigger" },
  { type: "llm_agent", label: "LLM Agent" },
  { type: "decision", label: "Decision" },
  { type: "api_action", label: "API Action" },
  { type: "slack", label: "Slack" },
  { type: "notion", label: "Notion" },
  { type: "email", label: "Email" },
  { type: "delay", label: "Delay" },
  { type: "human_approval", label: "Human Approval" },
];

export default function BuilderPage() {
  const token = useAuthStore((s) => s.token);

  const [name, setName] = useState("AI Demo Workflow");
  const [inputText, setInputText] = useState("Whenever a Slack message contains invoice details, extract them and create an ERP entry.");
  const [workflowId, setWorkflowId] = useState<string | null>(null);

  const initialNodes = useMemo<Node[]>(
    () => [
      {
        id: makeNodeId(),
        type: "trigger",
        position: { x: 0, y: 0 },
        data: { label: "Slack Trigger", node_data: { source: "slack" } },
      },
      {
        id: makeNodeId(),
        type: "llm_agent",
        position: { x: 250, y: 0 },
        data: {
          label: "Summarizer",
          node_data: { agent_kind: "summarizer", prompt: "Summarize and extract key fields. Return JSON." },
        },
      },
    ],
    [],
  );

  const initialEdges = useMemo<Edge[]>(() => [], []);

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [saving, setSaving] = useState(false);
  const [executing, setExecuting] = useState(false);
  const [execution, setExecution] = useState<any>(null);
  const [polling, setPolling] = useState(false);

  const toWorkflowPayload = () => {
    const req = {
      name,
      description: "Created in IntelliFlow builder",
      nodes: nodes.map((n) => ({
        id: n.id,
        type: n.type as NodeType,
        label: n.data?.label || n.type,
        position_x: Math.round(n.position.x),
        position_y: Math.round(n.position.y),
        data: n.data?.node_data || {},
      })),
      edges: edges.map((e) => ({
        from_node_id: String(e.source),
        to_node_id: String(e.target),
        condition_key: (e.data as any)?.condition_key ?? null,
        id: null,
      })),
    };
    return req;
  };

  async function onSave() {
    if (!token) return;
    setSaving(true);
    setExecution(null);
    try {
      const res = await createWorkflow(token, toWorkflowPayload());
      setWorkflowId(res.id);
    } finally {
      setSaving(false);
    }
  }

  async function onExecute() {
    if (!token || !workflowId) return;
    setExecuting(true);
    setPolling(true);
    setExecution(null);
    try {
      const res = await executeWorkflow(token, workflowId, { input_payload: { message: inputText, text: inputText } });
      setExecution({ execution_id: res.execution_id, status: res.status });

      // Poll execution until terminal state.
      const executionId = String(res.execution_id);
      let done = false;
      while (!done) {
        await new Promise((r) => setTimeout(r, 1500));
        const execRes = await (await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/executions/${executionId}`, {
          headers: { Authorization: `Bearer ${token}` },
        })).json();
        setExecution(execRes);
        if (execRes.status === "succeeded" || execRes.status === "failed") {
          done = true;
        }
      }
    } finally {
      setExecuting(false);
      setPolling(false);
    }
  }

  // ReactFlow handlers
  function onConnect(connection: any) {
    setEdges((eds) =>
      addEdge(
        {
          ...connection,
          id: makeNodeId(),
          data: {},
        },
        eds,
      ),
    );
  }

  function addNode(type: NodeType) {
    const id = makeNodeId();
    const lastX = nodes.reduce((acc, n) => Math.max(acc, n.position.x), 0);
    const newNode: Node = {
      id,
      type,
      position: { x: lastX + 250, y: Math.round(Math.random() * 250) },
      data: {
        label: type
          .split("_")
          .map((s) => s[0]?.toUpperCase() + s.slice(1))
          .join(" "),
        node_data:
          type === "llm_agent"
            ? { agent_kind: "summarizer", prompt: "Generate JSON output from input. Return summary + extracted." }
            : type === "notion"
              ? { title: "Task: {{summary}}", properties: { Status: "To do" } }
              : type === "slack"
                ? { channel: "general", text: "Summary: {{summary}}" }
                : type === "email"
                  ? { subject: "Re: {{summary}}", body_template: "Summary: {{summary}}" }
                  : {},
      },
    };
    setNodes((nds) => nds.concat(newNode));
  }

  return (
    <div className="space-y-4">
      <Card className="p-4">
        <div className="flex flex-col md:flex-row md:items-end gap-4 md:justify-between">
          <div className="space-y-2 flex-1">
            <div className="text-xs uppercase tracking-widest text-slate-300">Workflow Builder</div>
            <div className="text-xl font-semibold">Compose autonomous steps</div>
            <p className="text-slate-300 text-sm">Drag nodes, connect edges, then save + execute.</p>
          </div>
          <div className="flex gap-3 items-end">
            <div>
              <Label>Name</Label>
              <Input value={name} onChange={(e) => setName(e.target.value)} className="mt-1 w-72" />
            </div>
            <Button onClick={onSave} disabled={!token || saving} className="mt-5">
              {saving ? "Saving..." : workflowId ? "Saved" : "Save Workflow"}
            </Button>
          </div>
        </div>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-[280px_1fr] gap-4">
        <div className="space-y-3">
          <Card className="p-3">
            <div className="text-sm font-semibold">Add nodes</div>
            <div className="mt-3 grid grid-cols-2 gap-2">
              {PALETTE.map((p) => (
                <Button key={p.type} variant="secondary" onClick={() => addNode(p.type)}>
                  {p.label}
                </Button>
              ))}
            </div>
          </Card>

          <Card className="p-3">
            <div className="text-sm font-semibold">Execution input</div>
            <textarea
              className="mt-2 w-full h-28 rounded-xl border border-white/10 bg-black/20 px-3 py-2 outline-none"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
            />

            <div className="mt-3 flex items-center gap-3">
              <Button onClick={onExecute} disabled={!token || !workflowId || executing} className="flex-1">
                {executing ? "Executing..." : "Run Workflow"}
              </Button>
            </div>

            {polling ? <div className="text-xs text-slate-400 mt-2">Polling execution…</div> : null}
          </Card>

          {execution?.status ? (
            <Card className="p-3">
              <div className="text-sm font-semibold">Execution</div>
              <div className="text-slate-300 text-sm mt-2">Status: {execution.status}</div>
              {execution.error_text ? <div className="text-red-300 text-sm mt-2">{execution.error_text}</div> : null}
            </Card>
          ) : null}
        </div>

        <Card className="p-0 overflow-hidden">
          <div className="h-[650px] w-full">
            <ReactFlow
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onConnect={onConnect}
              fitView
              attributionPosition="bottom-right"
            >
              <Background gap={16} />
              <Controls />
            </ReactFlow>
          </div>
        </Card>
      </div>
    </div>
  );
}

