"""Create or reconfigure ElevenLabs agents before the orchestrator starts."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import os
import sys
from typing import Any

from elevenlabs.client import ElevenLabs
from elevenlabs.types import AgentPlatformSettingsRequestModel, AuthSettings, ConversationalConfig

from app.config import Settings, settings
from app.db import Store
from prompts import AGENT_NEGOTIATOR_FIRST_MESSAGE, AGENT_NEGOTIATOR_SYSTEM_PROMPT

AGENT_ID_KEY = "elevenlabs_agent_negotiator_id"
PROMPT_HASH_KEY = "elevenlabs_agent_negotiator_prompt_sha256"
AGENT_NAME = "The Negotiator — Agent Negotiator"


@dataclass(frozen=True)
class ProvisioningResult:
    agent_id: str
    action: str
    prompt_sha256: str


def _conversation_config(llm: str) -> ConversationalConfig:
    return ConversationalConfig(
        agent={
            "first_message": AGENT_NEGOTIATOR_FIRST_MESSAGE,
            "language": "en",
            "prompt": {
                "prompt": AGENT_NEGOTIATOR_SYSTEM_PROMPT,
                "llm": llm,
                "temperature": 0.2,
            },
        }
    )


def _platform_settings() -> AgentPlatformSettingsRequestModel:
    # Private agents require a server-issued signed URL in the browser widget.
    return AgentPlatformSettingsRequestModel(auth=AuthSettings(enable_auth=True))


def _status_code(error: Exception) -> int | None:
    for attribute in ("status_code", "status"):
        value = getattr(error, attribute, None)
        if isinstance(value, int):
            return value
    body = getattr(error, "body", None)
    if isinstance(body, dict) and isinstance(body.get("status_code"), int):
        return body["status_code"]
    return None


def _as_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if hasattr(value, "model_dump"):
        return value.model_dump(exclude_none=True)
    if hasattr(value, "__dict__"):
        return dict(value.__dict__)
    raise RuntimeError("unexpected ElevenLabs agent response")


def _verify_remote_agent(api: Any, agent_id: str) -> None:
    remote = _as_dict(api.conversational_ai.agents.get(agent_id))
    if remote.get("agent_id") != agent_id:
        raise RuntimeError("ElevenLabs verification returned a different agent_id")
    conversation = _as_dict(remote.get("conversation_config", {}))
    agent = _as_dict(conversation.get("agent", {}))
    prompt = _as_dict(agent.get("prompt", {}))
    if prompt.get("prompt") != AGENT_NEGOTIATOR_SYSTEM_PROMPT:
        raise RuntimeError("ElevenLabs Agent Negotiator prompt verification failed")
    if agent.get("first_message") != AGENT_NEGOTIATOR_FIRST_MESSAGE:
        raise RuntimeError("ElevenLabs Agent Negotiator first-message verification failed")


def provision_agent_negotiator(
    *,
    store: Store,
    config: Settings,
    client: Any | None = None,
) -> ProvisioningResult:
    if not config.elevenlabs_api_key:
        raise RuntimeError("ELEVENLABS_API_KEY is required to provision Agent Negotiator")

    api = client or ElevenLabs(api_key=config.elevenlabs_api_key)
    agent_id = store.get_setting(AGENT_ID_KEY)
    conversation_config = _conversation_config(config.elevenlabs_agent_negotiator_llm)
    platform_settings = _platform_settings()
    action = "updated"

    if agent_id:
        try:
            api.conversational_ai.agents.get(agent_id)
            response = api.conversational_ai.agents.update(
                agent_id,
                conversation_config=conversation_config,
                platform_settings=platform_settings,
                name=AGENT_NAME,
                version_description="Sync from orchestrator/prompts.py",
            )
            agent_id = getattr(response, "agent_id", None) or agent_id
        except Exception as exc:
            if _status_code(exc) != 404:
                raise RuntimeError(f"could not update ElevenLabs Agent Negotiator: {exc}") from exc
            agent_id = None

    if not agent_id:
        try:
            response = api.conversational_ai.agents.create(
                conversation_config=conversation_config,
                platform_settings=platform_settings,
                name=AGENT_NAME,
                tags=["hack-nation", "negotiator", "agent-negotiator"],
            )
        except Exception as exc:
            raise RuntimeError(f"could not create ElevenLabs Agent Negotiator: {exc}") from exc
        agent_id = getattr(response, "agent_id", None)
        if not agent_id:
            raise RuntimeError("ElevenLabs create agent response did not contain agent_id")
        action = "created"

    _verify_remote_agent(api, agent_id)
    prompt_hash = hashlib.sha256(f"{AGENT_NEGOTIATOR_SYSTEM_PROMPT}\n{AGENT_NEGOTIATOR_FIRST_MESSAGE}".encode()).hexdigest()
    store.set_setting(AGENT_ID_KEY, agent_id)
    store.set_setting(PROMPT_HASH_KEY, prompt_hash)
    return ProvisioningResult(agent_id=agent_id, action=action, prompt_sha256=prompt_hash)


def main() -> None:
    store = Store(settings.database_path)
    result = provision_agent_negotiator(store=store, config=settings)
    print(f"Agent Negotiator {result.action}: {result.agent_id}", flush=True)

    if "--serve" in sys.argv:
        os.execvp(
            "uvicorn",
            ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"],
        )


if __name__ == "__main__":
    main()
