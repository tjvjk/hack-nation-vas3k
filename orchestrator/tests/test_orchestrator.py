from dataclasses import replace
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace

os.environ["ORCHESTRATOR_DATA_DIR"] = tempfile.mkdtemp(prefix="negotiator-tests-")

from app.config import settings
from app.db import Store
from app.domain import MoveCreate, QuoteResult
from create_agents import AGENT_ID_KEY, provision_agent_negotiator
from prompts import AGENT_NEGOTIATOR_FIRST_MESSAGE, AGENT_NEGOTIATOR_SYSTEM_PROMPT


def payload(**overrides):
    data = {
        "origin": "San Francisco, CA 94110",
        "destination": "San Jose, CA 95113",
        "move_date": "2026-08-01",
        "budget_min": 1600,
        "budget_max": 2600,
        "service_type": "truck_and_movers",
        "bedrooms": 2,
        "movers_count": 2,
        "origin_floor": 2,
        "destination_floor": 1,
        "origin_elevator": False,
        "destination_elevator": True,
        "long_carry": False,
        "parking_constraints": "",
        "inventory": [{"name": "Sofa", "quantity": 1, "large": True}],
        "notes": "",
        "confirmed": True,
        "outreach_consent": True,
        "max_carriers": 3,
    }
    data.update(overrides)
    return data


def fresh_store():
    return Store(Path(tempfile.mkdtemp()) / "test.db")


def test_consent_is_required():
    try:
        MoveCreate.model_validate(payload(outreach_consent=False))
        raise AssertionError("validation should fail")
    except ValueError:
        pass


def test_campaign_is_idempotent_and_sequential():
    store = fresh_store()
    move = store.create_move(MoveCreate.model_validate(payload()).model_dump(mode="json"))
    first = store.start_campaign(move["id"])
    second = store.start_campaign(move["id"])
    assert first["id"] == second["id"]
    assert [job["status"] for job in first["jobs"]] == [
        "offered_to_widget",
        "scheduled",
        "scheduled",
    ]


def test_answer_is_compare_and_swap():
    store = fresh_store()
    move = store.create_move(MoveCreate.model_validate(payload()).model_dump(mode="json"))
    call_id = store.start_campaign(move["id"])["jobs"][0]["id"]
    assert store.answer_call(call_id)["status"] == "in_progress"
    try:
        store.answer_call(call_id)
        raise AssertionError("second answer should fail")
    except ValueError:
        pass


def test_lowball_is_flagged_and_not_recommended():
    store = fresh_store()
    move = store.create_move(MoveCreate.model_validate(payload()).model_dump(mode="json"))
    campaign = store.start_campaign(move["id"])
    first, second = campaign["jobs"][:2]
    store.answer_call(first["id"])
    store.finish_call(
        first["id"],
        QuoteResult(outcome="itemized_quote", initial_total=1200, final_total=900).model_dump(mode="json"),
    )
    store.answer_call(second["id"])
    store.finish_call(
        second["id"],
        QuoteResult(outcome="itemized_quote", initial_total=2200, final_total=1900).model_dump(mode="json"),
    )
    ranking = store.get_campaign(campaign["id"])["ranking"]
    assert "suspicious_lowball" in next(item for item in ranking if item["call_id"] == first["id"])["red_flags"]
    assert next(item for item in ranking if item["call_id"] == second["id"])["recommended"]


def test_webhook_event_is_idempotent():
    store = fresh_store()
    assert store.store_webhook("post_call_transcription:abc", {"data": 1})
    assert not store.store_webhook("post_call_transcription:abc", {"data": 2})


class _ApiNotFoundError(Exception):
    def __init__(self, message: str = "not found"):
        super().__init__(message)
        self.status_code = 404


class FakeAgents:
    def __init__(self):
        self.remote = {}
        self.created = 0
        self.updated = 0

    def create(self, *, conversation_config, **_):
        self.created += 1
        agent_id = f"agent-{self.created}"
        self.remote[agent_id] = conversation_config.model_dump(exclude_none=True)
        return SimpleNamespace(agent_id=agent_id)

    def get(self, agent_id):
        if agent_id not in self.remote:
            raise _ApiNotFoundError("not found")
        return {
            "agent_id": agent_id,
            "conversation_config": self.remote[agent_id],
        }

    def update(self, agent_id, *, conversation_config, **_):
        self.updated += 1
        self.remote[agent_id] = conversation_config.model_dump(exclude_none=True)
        return SimpleNamespace(agent_id=agent_id)


def test_agent_negotiator_is_created_then_reconfigured_from_sqlite():
    store = fresh_store()
    agents = FakeAgents()
    client = SimpleNamespace(conversational_ai=SimpleNamespace(agents=agents))
    config = replace(settings, elevenlabs_api_key="test-key")

    created = provision_agent_negotiator(store=store, config=config, client=client)
    assert created.action == "created"
    assert store.get_setting(AGENT_ID_KEY) == created.agent_id
    remote = agents.get(created.agent_id)["conversation_config"]["agent"]
    assert remote["prompt"]["prompt"] == AGENT_NEGOTIATOR_SYSTEM_PROMPT
    assert remote["first_message"] == AGENT_NEGOTIATOR_FIRST_MESSAGE

    updated = provision_agent_negotiator(store=store, config=config, client=client)
    assert updated.action == "updated"
    assert updated.agent_id == created.agent_id
    assert agents.created == 1
    assert agents.updated == 1
