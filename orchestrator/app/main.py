from __future__ import annotations

import asyncio
import json

from mcp.server.fastmcp import FastMCP
from pydantic import ValidationError
from starlette.requests import Request
from starlette.responses import FileResponse, JSONResponse, StreamingResponse
from starlette.routing import Route
from starlette.staticfiles import StaticFiles
from starlette.types import Scope

from prompts import (
    AGENT_NEGOTIATOR_ANALYSIS_SCHEMA,
    AGENT_NEGOTIATOR_FIRST_MESSAGE,
    AGENT_NEGOTIATOR_SYSTEM_PROMPT,
)

from .config import settings
from .db import Store
from .domain import MoveCreate, QuoteResult
from .elevenlabs_client import ElevenLabsGateway, verify_webhook


class NoCacheStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope: Scope):
        response = await super().get_response(path, scope)
        response.headers["Cache-Control"] = "no-store"
        return response


store = Store(settings.database_path)
gateway = ElevenLabsGateway(settings)

mcp = FastMCP(
    "The Negotiator Agent Negotiator Tools",
    instructions="Tools are scoped to exactly one call by call_id and capability.",
    stateless_http=True,
    json_response=True,
    streamable_http_path="/mcp",
)


@mcp.tool()
def get_call_context(call_id: str, capability: str) -> dict:
    """Return immutable move, carrier, benchmark, and verified leverage for one call."""
    return store.call_context(call_id, capability)


@mcp.tool()
def record_call_started(call_id: str, capability: str, conversation_id: str) -> dict:
    """Associate the ElevenLabs conversation with a claimed call."""
    return store.record_started(call_id, capability, conversation_id)


@mcp.tool()
def save_quote_progress(call_id: str, capability: str, progress: dict) -> dict:
    """Persist an initial quote or fee details while the conversation is active."""
    return store.save_progress(call_id, capability, progress)


def _quote_result_from_payload(payload: dict) -> QuoteResult:
    normalized = dict(payload)
    for json_key, target_key in (
        ("fees_json", "fees"),
        ("included_services_json", "included_services"),
        ("excluded_services_json", "excluded_services"),
    ):
        if json_key in normalized and target_key not in normalized:
            normalized[target_key] = _json_list(normalized.get(json_key))
    return QuoteResult.model_validate(normalized)


@mcp.tool()
def save_negotiation_result(call_id: str, capability: str, result: dict) -> dict:
    """Persist the single structured terminal result for a call."""
    parsed = _quote_result_from_payload(result)
    return store.finish_call(call_id, parsed.model_dump(mode="json"), capability)


@mcp.tool()
def mark_call_failure(call_id: str, capability: str, reason: str) -> dict:
    """Close a call with a structured technical failure."""
    return store.finish_call(
        call_id,
        QuoteResult(outcome="technical_failure", notes=reason).model_dump(mode="json"),
        capability,
    )


def error(message: str, status: int = 400, details=None) -> JSONResponse:
    body = {"error": message}
    if details is not None:
        body["details"] = details
    return JSONResponse(body, status_code=status)


async def homepage(_: Request):
    return FileResponse(settings.static_dir / "index.html", headers={"Cache-Control": "no-store"})


async def health(_: Request):
    agent_id = store.get_setting("elevenlabs_agent_negotiator_id")
    return JSONResponse(
        {
            "status": "ok",
            "live_agent": bool(agent_id),
            "agent_negotiator_configured": bool(agent_id),
            "transport": settings.call_transport,
        }
    )


async def state(_: Request):
    return JSONResponse(store.snapshot())


async def agent_negotiator_config(_: Request):
    return JSONResponse(
        {
            "system_prompt": AGENT_NEGOTIATOR_SYSTEM_PROMPT,
            "first_message": AGENT_NEGOTIATOR_FIRST_MESSAGE,
            "analysis_schema": AGENT_NEGOTIATOR_ANALYSIS_SCHEMA,
            "dynamic_variables": ["call_id", "call_capability", "move_context"],
            "agent_id": store.get_setting("elevenlabs_agent_negotiator_id"),
            "mcp_url": f"{settings.public_base_url.rstrip('/')}/mcp",
            "webhook_url": f"{settings.public_base_url.rstrip('/')}/webhooks/elevenlabs",
        }
    )


async def create_move(request: Request):
    try:
        parsed = MoveCreate.model_validate(await request.json())
    except ValidationError as exc:
        return error("invalid move specification", 422, exc.errors(include_url=False))
    except json.JSONDecodeError as exc:
        return error("invalid json in move specification", 422, str(exc))
    return JSONResponse(store.create_move(parsed.model_dump(mode="json")), status_code=201)


async def start_campaign(request: Request):
    try:
        campaign = store.start_campaign(request.path_params["move_id"])
    except KeyError as exc:
        return error(str(exc), 404)
    except ValueError as exc:
        return error(str(exc), 409)
    return JSONResponse(campaign, status_code=201)


async def answer_call(request: Request):
    call_id = request.path_params["call_id"]
    try:
        claim = store.answer_call(call_id)
    except KeyError as exc:
        return error(str(exc), 404)
    except ValueError as exc:
        return error(str(exc), 409)
    try:
        variables = store.session_variables(call_id, claim["claim_token"])
        agent_id = store.get_setting("elevenlabs_agent_negotiator_id")
        signed_url = await gateway.get_signed_url(agent_id)
        if not signed_url:
            raise RuntimeError("Agent Negotiator is not configured")
    except Exception as exc:
        try:
            store.release_call(call_id, claim["claim_token"])
        except (KeyError, ValueError):
            pass
        return error(f"could not create ElevenLabs session: {exc}", 502)
    return JSONResponse(
        {
            "mode": "live",
            "signed_url": signed_url,
            "dynamic_variables": variables,
            "claim_token": claim["claim_token"],
        }
    )


async def call_started(request: Request):
    try:
        body = await request.json()
        claim_token = body.get("claim_token")
        conversation_id = body.get("conversation_id")
        if not isinstance(claim_token, str) or not isinstance(conversation_id, str):
            return error("claim_token and conversation_id are required", 422)
        result = store.start_call(request.path_params["call_id"], claim_token, conversation_id)
    except json.JSONDecodeError as exc:
        return error("invalid json", 422, str(exc))
    except KeyError as exc:
        return error(str(exc), 404)
    except ValueError as exc:
        return error(str(exc), 409)
    return JSONResponse(result)


async def release_call(request: Request):
    try:
        body = await request.json()
        claim_token = body.get("claim_token")
        if not isinstance(claim_token, str):
            return error("claim_token is required", 422)
        result = store.release_call(request.path_params["call_id"], claim_token)
    except json.JSONDecodeError as exc:
        return error("invalid json", 422, str(exc))
    except KeyError as exc:
        return error(str(exc), 404)
    except ValueError as exc:
        return error(str(exc), 409)
    return JSONResponse(result)


async def call_session(request: Request):
    call_id = request.path_params["call_id"]
    try:
        claim_token = store.current_claim_token(call_id)
        variables = store.session_variables(call_id, claim_token)
        agent_id = store.get_setting("elevenlabs_agent_negotiator_id")
        signed_url = await gateway.get_signed_url(agent_id)
        if not signed_url:
            raise RuntimeError("Agent Negotiator is not configured")
    except KeyError as exc:
        return error(str(exc), 404)
    except ValueError as exc:
        return error(str(exc), 409)
    except Exception as exc:
        return error(f"could not create ElevenLabs session: {exc}", 502)
    return JSONResponse({"mode": "live", "signed_url": signed_url, "dynamic_variables": variables})


async def decline_call(request: Request):
    call_id = request.path_params["call_id"]
    try:
        store.answer_call(call_id)
        result = store.finish_call(
            call_id,
            QuoteResult(outcome="documented_decline", notes="Declined in carrier widget").model_dump(mode="json"),
        )
    except KeyError as exc:
        return error(str(exc), 404)
    except ValueError as exc:
        return error(str(exc), 409)
    return JSONResponse(result)


async def call_result(request: Request):
    try:
        parsed = _quote_result_from_payload(await request.json())
        result = store.finish_call(request.path_params["call_id"], parsed.model_dump(mode="json"))
    except ValidationError as exc:
        return error("invalid call result", 422, exc.errors(include_url=False))
    except json.JSONDecodeError as exc:
        return error("invalid json in call result", 422, str(exc))
    except KeyError as exc:
        return error(str(exc), 404)
    return JSONResponse(result)


async def call_progress(request: Request):
    try:
        body = await request.json()
        if not isinstance(body, dict):
            return error("progress must be a JSON object", 422)
        result = store.save_progress(request.path_params["call_id"], None, body)
    except json.JSONDecodeError as exc:
        return error("invalid json in call progress", 422, str(exc))
    except KeyError as exc:
        return error(str(exc), 404)
    return JSONResponse(result)


def _analysis_values(details: dict) -> dict:
    analysis = details.get("analysis") or {}
    collected = analysis.get("data_collection_results") or {}
    values = {}
    for name, record in collected.items():
        values[name] = record.get("value") if isinstance(record, dict) else getattr(record, "value", None)
    return values


def _json_list(value) -> list:
    if isinstance(value, list):
        return value
    if not isinstance(value, str) or not value.strip():
        return []
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return []
    return parsed if isinstance(parsed, list) else []


def _quote_from_analysis(details: dict, conversation_id: str) -> QuoteResult | None:
    values = _analysis_values(details)
    outcome = values.get("outcome")
    if outcome == "documented_decline" and (
        values.get("initial_total") is not None or values.get("final_total") is not None
    ):
        outcome = "partial_decline"
    if outcome not in {
        "itemized_quote",
        "partial_decline",
        "callback_commitment",
        "documented_decline",
        "no_answer",
        "technical_failure",
    }:
        return None
    try:
        return QuoteResult(
            outcome=outcome,
            initial_total=values.get("initial_total"),
            final_total=values.get("final_total"),
            fees=_json_list(values.get("fees_json")),
            included_services=_json_list(values.get("included_services_json")),
            excluded_services=_json_list(values.get("excluded_services_json")),
            binding=values.get("binding") or "unknown",
            availability=values.get("availability") or "",
            deposit_terms=values.get("deposit_terms") or "",
            cancellation_terms=values.get("cancellation_terms") or "",
            quote_validity=values.get("quote_validity") or "",
            notes=values.get("notes") or "",
            conversation_id=conversation_id,
        )
    except ValidationError:
        return None


async def reconcile_call(request: Request):
    call_id = request.path_params["call_id"]
    try:
        conversation_id = store.conversation_id_for_call(call_id)
        if not conversation_id:
            return error("call has no ElevenLabs conversation", 409)
        details = await gateway.get_conversation_details(conversation_id)
    except KeyError as exc:
        return error(str(exc), 404)
    except Exception as exc:
        return error(f"could not retrieve ElevenLabs conversation: {exc}", 502)

    transcript = details.get("transcript")
    if isinstance(transcript, list):
        try:
            store.save_transcript(call_id, conversation_id, transcript)
        except ValueError as exc:
            return error(str(exc), 409)

    status = details.get("status")
    if status in {"initiated", "in-progress", "processing"}:
        return JSONResponse({"status": status, "reconciled": False}, status_code=202)
    if status == "failed":
        result = QuoteResult(
            outcome="technical_failure",
            notes="ElevenLabs conversation failed before a structured result was available.",
            conversation_id=conversation_id,
        )
    else:
        result = _quote_from_analysis(details, conversation_id)
        if result is None:
            summary = (details.get("analysis") or {}).get("transcript_summary") or ""
            result = QuoteResult(
                outcome="technical_failure",
                notes=(
                    "ElevenLabs conversation ended without a valid structured negotiation result."
                    + (f" Summary: {summary}" if summary else "")
                ),
                conversation_id=conversation_id,
            )
    saved = store.finish_call(call_id, result.model_dump(mode="json"))
    return JSONResponse({"status": status, "reconciled": True, "result": saved})


async def events(request: Request):
    async def stream():
        last = None
        while not await request.is_disconnected():
            payload = json.dumps(store.snapshot(), separators=(",", ":"))
            if payload != last:
                yield f"event: state\ndata: {payload}\n\n"
                last = payload
            else:
                yield ": keepalive\n\n"
            await asyncio.sleep(1)

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


async def elevenlabs_webhook(request: Request):
    raw_body = await request.body()
    try:
        payload = verify_webhook(
            raw_body,
            request.headers.get("ElevenLabs-Signature"),
            settings.elevenlabs_webhook_secret,
        )
    except ValueError:
        return error("invalid webhook signature or payload", 401)
    event_type = payload.get("type") or payload.get("event_type") or "unknown"
    data = payload.get("data") or payload
    conversation_id = data.get("conversation_id") or "unknown"
    event_key = f"{event_type}:{conversation_id}"
    inserted = store.store_webhook(event_key, payload)
    return JSONResponse({"ok": True, "idempotent": not inserted})


routes = [
    Route("/", homepage),
    Route("/health", health),
    Route("/api/state", state),
    Route("/api/agent_negotiator/config", agent_negotiator_config),
    Route("/api/events", events),
    Route("/api/moves", create_move, methods=["POST"]),
    Route("/api/moves/{move_id:str}/campaign", start_campaign, methods=["POST"]),
    Route("/api/calls/{call_id:str}/answer", answer_call, methods=["POST"]),
    Route("/api/calls/{call_id:str}/started", call_started, methods=["POST"]),
    Route("/api/calls/{call_id:str}/release", release_call, methods=["POST"]),
    Route("/api/calls/{call_id:str}/session", call_session),
    Route("/api/calls/{call_id:str}/decline", decline_call, methods=["POST"]),
    Route("/api/calls/{call_id:str}/progress", call_progress, methods=["POST"]),
    Route("/api/calls/{call_id:str}/result", call_result, methods=["POST"]),
    Route("/api/calls/{call_id:str}/reconcile", reconcile_call, methods=["POST"]),
    Route("/webhooks/elevenlabs", elevenlabs_webhook, methods=["POST"]),
]

app = mcp.streamable_http_app()
for route in reversed(routes):
    app.router.routes.insert(0, route)
app.mount("/static", NoCacheStaticFiles(directory=settings.static_dir), name="static")
