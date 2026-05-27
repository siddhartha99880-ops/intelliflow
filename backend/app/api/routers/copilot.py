from __future__ import annotations

import uuid
from fastapi import APIRouter, Depends, HTTPException

from app.agents.llm import run_llm_json
from app.api.deps import get_current_team

router = APIRouter()


@router.post("/chat", response_model=dict)
async def copilot_chat(body: dict, team=Depends(get_current_team)):
    message = body.get("message")
    context = body.get("context") or {}
    if not message:
        raise HTTPException(status_code=400, detail="Missing message")

    prompt = (
        "You are IntelliFlow Copilot inside a SaaS dashboard. "
        "Be concise and practical. If relevant, propose workflow steps and node configs."
    )
    res = await run_llm_json(kind="copilot_chat", prompt=prompt, input_payload={"message": message, "context": context})

    # If the LLM returned JSON, try to surface it nicely.
    out = res.get("output")
    if isinstance(out, dict) and "message" in out:
        return {"message": out.get("message"), "raw": out}
    if isinstance(out, dict) and "raw" in out:
        return {"message": str(out.get("raw")), "raw": out}
    return {"message": str(out), "raw": out}


def _demo_generated_graph(instruction: str) -> dict:
    """
    Deterministic fallback workflow generator so the feature works without OpenAI creds.
    Produces a simple trigger -> (optional extract) -> update_erp -> slack notify flow.
    """
    trigger_id = str(uuid.uuid4())
    llm_id = str(uuid.uuid4())
    erp_id = str(uuid.uuid4())
    slack_id = str(uuid.uuid4())

    lower = instruction.lower()
    trigger_source = "slack" if "slack" in lower else "generic"

    return {
        "name": f"Generated: {instruction[:48].strip()}".strip(),
        "description": "Generated from natural language (fallback template)",
        "nodes": [
            {
                "id": trigger_id,
                "type": "trigger",
                "label": f"{trigger_source.title()} Trigger",
                "position_x": 0,
                "position_y": 0,
                "data": {"source": trigger_source},
            },
            {
                "id": llm_id,
                "type": "llm_agent",
                "label": "Extract & Summarize",
                "position_x": 260,
                "position_y": 0,
                "data": {
                    "agent_kind": "decision",
                    "prompt": "Extract structured fields and create a concise summary. Return JSON {summary, extracted}.",
                },
            },
            {
                "id": erp_id,
                "type": "api_action",
                "label": "Update ERP",
                "position_x": 520,
                "position_y": 0,
                "data": {"action": "update_erp", "entry_type": "finance_entries"},
            },
            {
                "id": slack_id,
                "type": "slack",
                "label": "Notify in Slack",
                "position_x": 780,
                "position_y": 0,
                "data": {"channel": "general", "text": "ERP updated. Summary: {{summary}}"},
            },
        ],
        "edges": [
            {"id": None, "from_node_id": trigger_id, "to_node_id": llm_id, "condition_key": None},
            {"id": None, "from_node_id": llm_id, "to_node_id": erp_id, "condition_key": None},
            {"id": None, "from_node_id": erp_id, "to_node_id": slack_id, "condition_key": None},
        ],
    }


@router.post("/generate-workflow", response_model=dict)
async def copilot_generate_workflow(body: dict, team=Depends(get_current_team)):
    instruction = body.get("instruction")
    if not instruction:
        raise HTTPException(status_code=400, detail="Missing instruction")

    prompt = (
        "You generate IntelliFlow workflow graphs for a React Flow builder.\n"
        "Return ONLY valid JSON with keys: name, description, nodes, edges.\n"
        "nodes[].type must be one of: trigger, llm_agent, decision, api_action, slack, notion, email, delay, human_approval.\n"
        "nodes[].data is the node configuration.\n"
        "edges[].condition_key is optional; use it for decision branching.\n"
        "Ensure there is exactly one trigger node and the graph is connected.\n"
    )

    res = await run_llm_json(kind="copilot_generate_workflow", prompt=prompt, input_payload={"instruction": instruction})
    out = res.get("output")

    # If the model didn't return structured JSON, fall back to deterministic template.
    if not isinstance(out, dict) or "nodes" not in out or "edges" not in out:
        return _demo_generated_graph(instruction)

    # Basic validation/sanitization
    allowed_types = {
        "trigger",
        "llm_agent",
        "decision",
        "api_action",
        "slack",
        "notion",
        "email",
        "delay",
        "human_approval",
    }

    nodes = out.get("nodes") or []
    edges = out.get("edges") or []
    if not isinstance(nodes, list) or not isinstance(edges, list):
        return _demo_generated_graph(instruction)

    # Normalize node IDs to UUID strings
    normalized_nodes = []
    trigger_count = 0
    for n in nodes:
        if not isinstance(n, dict):
            continue
        ntype = n.get("type")
        if ntype not in allowed_types:
            continue
        nid = n.get("id") or str(uuid.uuid4())
        try:
            nid = str(uuid.UUID(str(nid)))
        except Exception:
            nid = str(uuid.uuid4())
        if ntype == "trigger":
            trigger_count += 1
        normalized_nodes.append(
            {
                "id": nid,
                "type": ntype,
                "label": n.get("label") or ntype,
                "position_x": int(n.get("position_x") or 0),
                "position_y": int(n.get("position_y") or 0),
                "data": n.get("data") or {},
            }
        )

    if trigger_count != 1:
        return _demo_generated_graph(instruction)

    node_ids = {n["id"] for n in normalized_nodes}
    normalized_edges = []
    for e in edges:
        if not isinstance(e, dict):
            continue
        src = e.get("from_node_id")
        dst = e.get("to_node_id")
        if not src or not dst:
            continue
        try:
            src = str(uuid.UUID(str(src)))
            dst = str(uuid.UUID(str(dst)))
        except Exception:
            continue
        if src not in node_ids or dst not in node_ids:
            continue
        normalized_edges.append(
            {
                "id": None,
                "from_node_id": src,
                "to_node_id": dst,
                "condition_key": e.get("condition_key"),
            }
        )

    return {
        "name": out.get("name") or f"Generated: {instruction[:48].strip()}",
        "description": out.get("description") or "Generated from natural language",
        "nodes": normalized_nodes,
        "edges": normalized_edges,
    }

