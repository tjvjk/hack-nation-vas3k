from dataclasses import replace
from datetime import UTC, datetime, timedelta
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace

import pytest
from starlette.testclient import TestClient

os.environ["ORCHESTRATOR_DATA_DIR"] = tempfile.mkdtemp(prefix="negotiator-tests-")

from app import main as main_module
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
    claim = store.answer_call(call_id)
    assert claim["status"] == "claimed"
    try:
        store.answer_call(call_id)
        raise AssertionError("second answer should fail")
    except ValueError:
        pass
    assert store.release_call(call_id, claim["claim_token"])["status"] == "offered_to_widget"
    retry = store.answer_call(call_id)
    assert retry["claim_token"] != claim["claim_token"]
    started = store.start_call(call_id, retry["claim_token"], "conversation-1")
    assert started["status"] == "in_progress"
    assert store.start_call(call_id, retry["claim_token"], "conversation-1")["idempotent"]
    try:
        store.release_call(call_id, retry["claim_token"])
        raise AssertionError("a started call must not be released")
    except ValueError:
        pass


def test_session_variables_include_confirmed_move_context_without_private_pricing():
    store = fresh_store()
    move = store.create_move(MoveCreate.model_validate(payload()).model_dump(mode="json"))
    call_id = store.start_campaign(move["id"])["jobs"][0]["id"]
    claim = store.answer_call(call_id)

    variables = store.session_variables(call_id, claim["claim_token"])
    context = json.loads(variables["move_context"])

    assert context["move_spec"]["origin"] == payload()["origin"]
    assert context["move_spec"]["destination"] == payload()["destination"]
    assert context["move_spec"]["inventory"] == payload()["inventory"]
    assert context["move_spec"]["budget_min"] == payload()["budget_min"]
    assert context["move_spec"]["budget_max"] == payload()["budget_max"]
    assert "private_brief" not in context["carrier"]
    assert "floor" not in json.dumps(context["carrier"]).lower()


def test_second_carrier_receives_first_verified_quote_as_honest_leverage():
    store = fresh_store()
    move = store.create_move(MoveCreate.model_validate(payload()).model_dump(mode="json"))
    campaign = store.start_campaign(move["id"])
    first, second = campaign["jobs"][:2]
    store.answer_call(first["id"])
    store.finish_call(
        first["id"],
        QuoteResult(
            outcome="itemized_quote",
            initial_total=2350,
            final_total=2050,
            fees=[{"name": "stairs", "amount": 150}],
            included_services=["truck", "two movers"],
            excluded_services=["packing"],
            binding="non_binding",
            availability="Available on requested date",
            deposit_terms="$200 refundable deposit",
            cancellation_terms="Full refund until 48 hours before move",
            quote_validity="7 days",
        ).model_dump(mode="json"),
    )
    claim = store.answer_call(second["id"])

    context = json.loads(store.session_variables(second["id"], claim["claim_token"])["move_context"])

    assert context["move_spec"]["budget_max"] == 2600
    assert context["verified_quotes"] == [
        {
            "carrier_name": "DIXIE MOVING & STORAGE CO INC",
            "quote_quality": "itemized",
            "initial_total": 2350.0,
            "final_total": 2050.0,
            "currency": "USD",
            "fees": [{"name": "stairs", "amount": 150}],
            "included_services": ["truck", "two movers"],
            "excluded_services": ["packing"],
            "binding": "non_binding",
            "availability": "Available on requested date",
            "deposit_terms": "$200 refundable deposit",
            "cancellation_terms": "Full refund until 48 hours before move",
            "quote_validity": "7 days",
        }
    ]


def test_campaign_uses_active_fmcsa_directory_records():
    store = fresh_store()
    move = store.create_move(MoveCreate.model_validate(payload()).model_dump(mode="json"))

    carriers = [job["carrier"] for job in store.start_campaign(move["id"])["jobs"]]

    assert [carrier["dot_number"] for carrier in carriers] == ["285683", "300453", "302292"]
    assert all(carrier["source"] == "FMCSA Company Census" for carrier in carriers)
    assert all("simulated counterparty" in carrier["headline"] for carrier in carriers)


def test_partial_decline_price_is_available_as_preliminary_leverage():
    store = fresh_store()
    move = store.create_move(MoveCreate.model_validate(payload()).model_dump(mode="json"))
    first, second = store.start_campaign(move["id"])["jobs"][:2]
    store.answer_call(first["id"])
    store.finish_call(
        first["id"],
        QuoteResult(
            outcome="partial_decline",
            initial_total=100,
            final_total=10_000,
            notes="Carrier stated prices but declined an itemized breakdown.",
        ).model_dump(mode="json"),
    )
    claim = store.answer_call(second["id"])

    quote = json.loads(store.session_variables(second["id"], claim["claim_token"])["move_context"])["verified_quotes"][0]

    assert quote["quote_quality"] == "preliminary_unitemized"
    assert quote["final_total"] == 10_000


def test_partial_decline_upgrades_prior_documented_decline():
    store = fresh_store()
    move = store.create_move(MoveCreate.model_validate(payload()).model_dump(mode="json"))
    call_id = store.start_campaign(move["id"])["jobs"][0]["id"]
    store.answer_call(call_id)
    store.finish_call(call_id, QuoteResult(outcome="documented_decline").model_dump(mode="json"))

    upgraded = store.finish_call(
        call_id,
        QuoteResult(outcome="partial_decline", final_total=10_000).model_dump(mode="json"),
    )

    assert upgraded["status"] == "completed"
    result = store.snapshot()["campaigns"][0]["jobs"][0]["result"]
    assert result["outcome"] == "partial_decline"
    assert result["final_total"] == 10_000


def test_stale_claim_is_automatically_released():
    store = fresh_store()
    move = store.create_move(MoveCreate.model_validate(payload()).model_dump(mode="json"))
    call_id = store.start_campaign(move["id"])["jobs"][0]["id"]
    store.answer_call(call_id)
    stale_at = (datetime.now(UTC) - timedelta(minutes=5)).isoformat()
    with store.connect() as db:
        db.execute("UPDATE call_jobs SET updated_at=? WHERE id=?", (stale_at, call_id))

    job = store.snapshot()["campaigns"][0]["jobs"][0]

    assert job["status"] == "offered_to_widget"


class FakeGateway:
    def __init__(self, results):
        self.results = iter(results)
        self.call_count = 0

    async def get_signed_url(self, _agent_id):
        self.call_count += 1
        result = next(self.results)
        if isinstance(result, Exception):
            raise result
        return result


class FakeConversationGateway(FakeGateway):
    def __init__(self, details):
        super().__init__(["wss://signed.test"])
        self.details = details

    async def get_conversation_details(self, _conversation_id):
        return self.details


@pytest.fixture(scope="module")
def client():
    with TestClient(main_module.app) as test_client:
        yield test_client


def api_call(monkeypatch, gateway):
    store = fresh_store()
    move = store.create_move(MoveCreate.model_validate(payload()).model_dump(mode="json"))
    call_id = store.start_campaign(move["id"])["jobs"][0]["id"]
    store.set_setting("elevenlabs_agent_negotiator_id", "agent-test")
    monkeypatch.setattr(main_module, "store", store)
    monkeypatch.setattr(main_module, "gateway", gateway)
    return store, call_id


def test_session_start_failure_releases_call(monkeypatch, client):
    gateway = FakeGateway([RuntimeError("signed URL unavailable")])
    store, call_id = api_call(monkeypatch, gateway)

    response = client.post(f"/api/calls/{call_id}/answer")

    assert response.status_code == 502
    job = store.snapshot()["campaigns"][0]["jobs"][0]
    assert job["status"] == "offered_to_widget"
    assert job["conversation_id"] is None


def test_session_start_can_be_retried_after_failure(monkeypatch, client):
    gateway = FakeGateway([RuntimeError("temporary failure"), "wss://signed.test"])
    store, call_id = api_call(monkeypatch, gateway)

    assert client.post(f"/api/calls/{call_id}/answer").status_code == 502
    answer = client.post(f"/api/calls/{call_id}/answer")
    assert answer.status_code == 200
    body = answer.json()
    started = client.post(
        f"/api/calls/{call_id}/started",
        json={"claim_token": body["claim_token"], "conversation_id": "conversation-retry"},
    )

    assert started.status_code == 200
    assert store.snapshot()["campaigns"][0]["jobs"][0]["status"] == "in_progress"


def test_legacy_session_endpoint_supports_cached_client(monkeypatch, client):
    gateway = FakeGateway(["wss://first.test", "wss://legacy.test"])
    _, call_id = api_call(monkeypatch, gateway)

    answer = client.post(f"/api/calls/{call_id}/answer")
    legacy_session = client.get(f"/api/calls/{call_id}/session")

    assert answer.status_code == 200
    assert legacy_session.status_code == 200
    assert legacy_session.json()["signed_url"] == "wss://legacy.test"
    assert gateway.call_count == 2


def test_successful_session_start_is_single_use(monkeypatch, client):
    gateway = FakeGateway(["wss://signed.test"])
    store, call_id = api_call(monkeypatch, gateway)

    answer = client.post(f"/api/calls/{call_id}/answer")
    assert answer.status_code == 200
    body = answer.json()
    started = client.post(
        f"/api/calls/{call_id}/started",
        json={"claim_token": body["claim_token"], "conversation_id": "conversation-once"},
    )
    duplicate = client.post(f"/api/calls/{call_id}/answer")

    assert started.status_code == 200
    assert duplicate.status_code == 409
    assert gateway.call_count == 1
    job = store.snapshot()["campaigns"][0]["jobs"][0]
    assert job["status"] == "in_progress"
    assert job["conversation_id"] == "conversation-once"


def test_client_tool_progress_and_result_advance_campaign(monkeypatch, client):
    gateway = FakeGateway(["wss://signed.test"])
    store, call_id = api_call(monkeypatch, gateway)
    answer = client.post(f"/api/calls/{call_id}/answer").json()
    client.post(
        f"/api/calls/{call_id}/started",
        json={"claim_token": answer["claim_token"], "conversation_id": "conversation-tools"},
    )

    progress = client.post(
        f"/api/calls/{call_id}/progress",
        json={"initial_total": 2300, "fees": [{"name": "fuel", "amount": 100}]},
    )
    result = client.post(
        f"/api/calls/{call_id}/result",
        json={
            "outcome": "itemized_quote",
            "initial_total": 2300,
            "final_total": 2050,
            "fees": [{"name": "fuel", "amount": 100}],
            "binding": "non_binding",
        },
    )

    assert progress.status_code == 200
    assert result.status_code == 200
    jobs = store.snapshot()["campaigns"][0]["jobs"]
    assert jobs[0]["status"] == "completed"
    assert jobs[0]["result"]["final_total"] == 2050
    assert jobs[1]["status"] == "offered_to_widget"


def test_reconciliation_saves_elevenlabs_data_collection(monkeypatch, client):
    gateway = FakeConversationGateway(
        {
            "status": "done",
            "transcript": [
                {"role": "agent", "message": "Please provide an itemized quote."},
                {"role": "user", "message": "The total is $2100."},
            ],
            "analysis": {
                "data_collection_results": {
                    "outcome": {"value": "itemized_quote"},
                    "initial_total": {"value": 2400},
                    "final_total": {"value": 2100},
                    "fees_json": {"value": '[{"name":"stairs","amount":150}]'},
                    "included_services_json": {"value": '["truck","labor"]'},
                    "binding": {"value": "non_binding"},
                    "availability": {"value": "Available"},
                }
            },
        }
    )
    store, call_id = api_call(monkeypatch, gateway)
    answer = client.post(f"/api/calls/{call_id}/answer").json()
    client.post(
        f"/api/calls/{call_id}/started",
        json={"claim_token": answer["claim_token"], "conversation_id": "conversation-analysis"},
    )

    response = client.post(f"/api/calls/{call_id}/reconcile")

    assert response.status_code == 200
    assert response.json()["reconciled"] is True
    result = store.snapshot()["campaigns"][0]["jobs"][0]["result"]
    assert result["final_total"] == 2100
    assert result["fees"] == [{"name": "stairs", "amount": 150}]
    assert result["included_services"] == ["truck", "labor"]
    assert store.snapshot()["campaigns"][0]["jobs"][0]["transcript"] == [
        {"role": "agent", "message": "Please provide an itemized quote."},
        {"role": "user", "message": "The total is $2100."},
    ]


def test_reconciliation_marks_done_call_without_result_as_technical_failure(monkeypatch, client):
    gateway = FakeConversationGateway(
        {
            "status": "done",
            "analysis": {"transcript_summary": "The call ended before the carrier provided a price."},
        }
    )
    store, call_id = api_call(monkeypatch, gateway)
    answer = client.post(f"/api/calls/{call_id}/answer").json()
    client.post(
        f"/api/calls/{call_id}/started",
        json={"claim_token": answer["claim_token"], "conversation_id": "conversation-incomplete"},
    )

    response = client.post(f"/api/calls/{call_id}/reconcile")

    assert response.status_code == 200
    assert response.json()["reconciled"] is True
    jobs = store.snapshot()["campaigns"][0]["jobs"]
    assert jobs[0]["status"] == "failed"
    assert jobs[0]["result"]["outcome"] == "technical_failure"
    assert "ended before the carrier provided a price" in jobs[0]["result"]["notes"]
    assert jobs[1]["status"] == "offered_to_widget"


def test_browser_demo_models_one_click_incoming_answer():
    static_dir = Path(__file__).parents[1] / "static"
    html = (static_dir / "index.html").read_text()
    javascript = (static_dir / "app.js").read_text()

    assert "Incoming call from The Negotiator" in html
    assert "You are answering as" in javascript
    assert "Conversation.startSession" in javascript
    assert "/started" in javascript
    assert "/release" in javascript
    assert "dynamicVariables: session.dynamic_variables" in javascript
    assert "clientTools:" in javascript
    assert "get_movebuddha_benchmark" in javascript
    assert "save_quote_progress" in javascript
    assert "save_negotiation_result" in javascript
    assert "resultSaved = true" in javascript
    assert "!resultSaved && isFarewell(message)" in javascript
    assert "endConversationSoon(activeConversation || pendingConversation);" not in javascript
    assert "isFarewell" in javascript
    assert "onMessage:" in javascript
    assert "enforceCallLimit" in javascript
    assert "180000" in javascript
    assert "animateIncomingAnswer" in javascript
    assert "answer.scrollIntoView" in javascript
    assert "answer.focus" in javascript
    assert "lastRenderedCallId" in javascript
    assert "campaignStartedThisPage" in javascript
    assert "campaign-started .hero" in (static_dir / "styles.css").read_text()
    assert "incoming-answer" in (static_dir / "styles.css").read_text()
    assert "Structured call records" in javascript
    assert 'id="call-results"' in html
    assert "/reconcile" in javascript
    assert "answer.disabled = false" in javascript
    assert 'answer.textContent = "Answer"' in javascript
    assert 'render(await api("/api/state"))' in javascript
    assert "{{move_context}}" in AGENT_NEGOTIATOR_SYSTEM_PROMPT
    assert "# Required workflow" in AGENT_NEGOTIATOR_SYSTEM_PROMPT
    assert "call save_quote_progress immediately" in AGENT_NEGOTIATOR_SYSTEM_PROMPT
    assert "There is no normal assistant" in AGENT_NEGOTIATOR_SYSTEM_PROMPT
    assert "confirmed move details" in AGENT_NEGOTIATOR_FIRST_MESSAGE
    assert "document.createElement(\"elevenlabs-convai\")" not in javascript
    assert "convai-widget-embed" not in html


def test_static_javascript_is_not_cached(client):
    response = client.get("/static/app.js")

    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"


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


class FakeTools:
    def __init__(self):
        self.remote = {}
        self.created = 0
        self.updated = 0

    def list(self, *, search, **_):
        tools = [tool for tool in self.remote.values() if tool.tool_config.name == search]
        return SimpleNamespace(tools=tools)

    def create(self, *, request):
        self.created += 1
        tool_id = f"tool-{self.created}"
        tool = SimpleNamespace(id=tool_id, tool_config=request.tool_config)
        self.remote[tool_id] = tool
        return tool

    def update(self, tool_id, *, request):
        self.updated += 1
        tool = SimpleNamespace(id=tool_id, tool_config=request.tool_config)
        self.remote[tool_id] = tool
        return tool


def test_agent_negotiator_is_created_then_reconfigured_from_sqlite():
    store = fresh_store()
    agents = FakeAgents()
    tools = FakeTools()
    client = SimpleNamespace(conversational_ai=SimpleNamespace(agents=agents, tools=tools))
    config = replace(settings, elevenlabs_api_key="test-key")

    created = provision_agent_negotiator(store=store, config=config, client=client)
    assert created.action == "created"
    assert store.get_setting(AGENT_ID_KEY) == created.agent_id
    remote = agents.get(created.agent_id)["conversation_config"]["agent"]
    assert remote["prompt"]["prompt"] == AGENT_NEGOTIATOR_SYSTEM_PROMPT
    assert remote["first_message"] == AGENT_NEGOTIATOR_FIRST_MESSAGE
    assert len(remote["prompt"]["tool_ids"]) == 3
    assert {tool.tool_config.name for tool in tools.remote.values()} == {
        "get_movebuddha_benchmark",
        "save_quote_progress",
        "save_negotiation_result",
    }
    client_tools = [tool for tool in tools.remote.values() if tool.tool_config.type == "client"]
    assert all(tool.tool_config.expects_response for tool in client_tools)
    result_tool = next(tool for tool in tools.remote.values() if tool.tool_config.name == "save_negotiation_result")
    assert result_tool.tool_config.execution_mode == "post_tool_speech"
    assert remote["prompt"]["built_in_tools"]["end_call"]["name"] == "end_call"
    assert remote["prompt"]["built_in_tools"]["end_call"]["pre_tool_speech"] == "force"

    updated = provision_agent_negotiator(store=store, config=config, client=client)
    assert updated.action == "updated"
    assert updated.agent_id == created.agent_id
    assert agents.created == 1
    assert agents.updated == 1
    assert tools.created == 3
    assert tools.updated == 3
