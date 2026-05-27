from __future__ import annotations

import asyncio
import uuid

from sqlalchemy import select

from app.core.config import get_settings
from app.core.database import async_session, engine
from app.core.security import hash_password
from app.models.team import Team, APIKey
from app.models.user import User
from app.models.workflow import Workflow, WorkflowEdge, WorkflowNode, WorkflowNodeType


async def seed() -> None:
    settings = get_settings()

    async with async_session() as session:
        # Team
        team_name = "Acme Ventures"
        res = await session.execute(select(Team).where(Team.name == team_name))
        team = res.scalar_one_or_none()
        if not team:
            team = Team(name=team_name)
            session.add(team)
            await session.commit()
            await session.refresh(team)

        # User
        email = "demo@intelliflow.local"
        res = await session.execute(select(User).where(User.email == email))
        user = res.scalar_one_or_none()
        if not user:
            user = User(
                email=email,
                hashed_password=hash_password("demo-password"),
                full_name="Demo User",
                team_id=team.id,
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)

            api_key = APIKey(name="demo", key=f"key_{user.id}", user_id=user.id)
            session.add(api_key)
            await session.commit()

        # Workflow template
        workflow_name = "Slack -> Summary -> Notion Task -> Email Draft"
        res = await session.execute(select(Workflow).where(Workflow.team_id == team.id, Workflow.name == workflow_name))
        workflow = res.scalar_one_or_none()
        if not workflow:
            workflow = Workflow(team_id=team.id, name=workflow_name, description="AI-assisted demo workflow")
            session.add(workflow)
            await session.commit()
            await session.refresh(workflow)

            trigger_id = uuid.uuid4()
            llm_id = uuid.uuid4()
            notion_id = uuid.uuid4()
            email_id = uuid.uuid4()

            session.add(
                WorkflowNode(
                    workflow_id=workflow.id,
                    id=trigger_id,
                    node_type=WorkflowNodeType.trigger,
                    label="Slack trigger",
                    pos_x=0,
                    pos_y=0,
                    node_data={"source": "slack"},
                )
            )
            session.add(
                WorkflowNode(
                    workflow_id=workflow.id,
                    id=llm_id,
                    node_type=WorkflowNodeType.llm_agent,
                    label="Summarize message",
                    pos_x=250,
                    pos_y=0,
                    node_data={
                        "agent_kind": "summarizer",
                        "prompt": "Summarize the slack message and extract key bullets for follow-up. Return JSON.",
                    },
                )
            )
            session.add(
                WorkflowNode(
                    workflow_id=workflow.id,
                    id=notion_id,
                    node_type=WorkflowNodeType.notion,
                    label="Create Notion task",
                    pos_x=500,
                    pos_y=0,
                    node_data={
                        "title": "Follow-up: {{summary}}",
                        "properties": {"Status": "To do", "Owner": "Demo"},
                    },
                )
            )
            session.add(
                WorkflowNode(
                    workflow_id=workflow.id,
                    id=email_id,
                    node_type=WorkflowNodeType.email,
                    label="Draft email",
                    pos_x=750,
                    pos_y=0,
                    node_data={
                        "subject": "Re: {{summary}}",
                        "body_template": "Hi team,\\n\\nSummary: {{summary}}\\n\\nNext steps:\\n- {{extracted}}\\n\\nRegards,\\nIntelliFlow",
                    },
                )
            )

            session.add(
                WorkflowEdge(workflow_id=workflow.id, from_node_id=trigger_id, to_node_id=llm_id, condition_key=None)
            )
            session.add(
                WorkflowEdge(workflow_id=workflow.id, from_node_id=llm_id, to_node_id=notion_id, condition_key=None)
            )
            session.add(
                WorkflowEdge(workflow_id=workflow.id, from_node_id=notion_id, to_node_id=email_id, condition_key=None)
            )

            await session.commit()

    print("Seed completed.")


if __name__ == "__main__":
    asyncio.run(seed())

