"""Create or reconfigure ElevenLabs agents before the orchestrator starts."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import os
import sys
from typing import Any, cast

from elevenlabs.client import ElevenLabs
from elevenlabs.types import (
    AgentConfig,
    AgentPlatformSettingsRequestModel,
    AnalysisProperty,
    AuthSettings,
    BuiltInToolsOutput,
    ConversationalConfig,
    LiteralJsonSchemaProperty,
    ObjectJsonSchemaPropertyInput,
    PromptAgentApiModelOutput,
    SystemToolConfigOutput,
    SystemToolConfigOutputParams_EndCall,
    ToolRequestModel,
    ToolRequestModelToolConfig_Client,
)

from app.config import Settings, settings
from app.db import Store
from prompts import AGENT_NEGOTIATOR_FIRST_MESSAGE, AGENT_NEGOTIATOR_SYSTEM_PROMPT

AGENT_ID_KEY = "elevenlabs_agent_negotiator_id"
PROMPT_HASH_KEY = "elevenlabs_agent_negotiator_prompt_sha256"
AGENT_NAME = "The Negotiator — Agent Negotiator"


CLIENT_TOOL_DEFINITIONS = {
    "save_quote_progress": {
        "description": "Save an initial carrier price or meaningful fee details while the call is active.",
        "required": [],
        "properties": {
            "initial_total": {"type": "number", "description": "Initial quoted total in USD."},
            "fees_json": {"type": "string", "description": "JSON array of itemized fee objects."},
            "notes": {"type": "string", "description": "Short factual progress note."},
        },
    },
    "save_negotiation_result": {
        "description": "Save the final structured carrier negotiation result exactly once before ending the call.",
        "tool_options": {
            "execution_mode": "post_tool_speech",
            "pre_tool_speech": "off",
            "interruption_mode": "disable_during_tool_and_turn",
        },
        "required": ["outcome"],
        "properties": {
            "outcome": {
                "type": "string",
                "enum": [
                    "itemized_quote",
                    "partial_decline",
                    "callback_commitment",
                    "documented_decline",
                    "no_answer",
                    "technical_failure",
                ],
                "description": "Terminal call outcome.",
            },
            "initial_total": {"type": "number", "description": "Initial quoted total in USD."},
            "final_total": {"type": "number", "description": "Final confirmed total in USD."},
            "fees_json": {"type": "string", "description": "JSON array of itemized fee objects."},
            "included_services_json": {"type": "string", "description": "JSON array of included service strings."},
            "excluded_services_json": {"type": "string", "description": "JSON array of excluded service strings."},
            "binding": {
                "type": "string",
                "enum": ["binding", "non_binding", "unknown"],
                "description": "Whether the carrier described the quote as binding.",
            },
            "availability": {"type": "string", "description": "Carrier availability for the requested date."},
            "deposit_terms": {"type": "string", "description": "Deposit amount and terms, without accepting them."},
            "cancellation_terms": {"type": "string", "description": "Cancellation and refund terms."},
            "quote_validity": {"type": "string", "description": "How long the quote remains valid."},
            "notes": {"type": "string", "description": "Other factual result details."},
        },
    },
}

END_CALL_DESCRIPTION = (
    "End the call after a completed quote or an explicit request to stop. "
    "This tool alone delivers the single final farewell. Speak one short outbound "
    "close to the carrier, for example: \"Thanks, I've got what I need. The "
    "customer will follow up if they proceed. Goodbye.\" Do not invite the carrier "
    "to ask questions or offer further help. Never say inbound-support phrases "
    "like \"If you need anything else\", \"let me know\", or \"further questions\"."
)


@dataclass(frozen=True)
class ProvisioningResult:
    agent_id: str
    action: str
    prompt_sha256: str


def _conversation_config(llm: str, tool_ids: list[str]) -> ConversationalConfig:
    return ConversationalConfig(
        agent=AgentConfig(
            first_message=AGENT_NEGOTIATOR_FIRST_MESSAGE,
            language="en",
            prompt=PromptAgentApiModelOutput(
                prompt=AGENT_NEGOTIATOR_SYSTEM_PROMPT,
                llm=llm,
                temperature=0.2,
                tool_ids=tool_ids,
                built_in_tools=BuiltInToolsOutput(
                    end_call=SystemToolConfigOutput(
                        name="end_call",
                        description=END_CALL_DESCRIPTION,
                        pre_tool_speech="force",
                        params=SystemToolConfigOutputParams_EndCall(),
                    )
                ),
            ),
        )
    )


def _platform_settings() -> AgentPlatformSettingsRequestModel:
    # Private agents require a server-issued signed URL in the browser widget.
    data_collection = {
        "outcome": AnalysisProperty(
            type="string",
            enum=CLIENT_TOOL_DEFINITIONS["save_negotiation_result"]["properties"]["outcome"]["enum"],
            description="Terminal outcome of the carrier conversation.",
        ),
        "initial_total": AnalysisProperty(type="number", description="Initial quoted total in USD; omit when absent."),
        "final_total": AnalysisProperty(type="number", description="Final confirmed total in USD; omit when absent."),
        "fees_json": AnalysisProperty(type="string", description="JSON array of itemized fees."),
        "included_services_json": AnalysisProperty(type="string", description="JSON array of included services."),
        "excluded_services_json": AnalysisProperty(type="string", description="JSON array of excluded services."),
        "binding": AnalysisProperty(
            type="string",
            enum=["binding", "non_binding", "unknown"],
            description="Whether the carrier described the quote as binding.",
        ),
        "availability": AnalysisProperty(type="string", description="Availability for the requested date."),
        "deposit_terms": AnalysisProperty(type="string", description="Deposit terms discussed."),
        "cancellation_terms": AnalysisProperty(type="string", description="Cancellation terms discussed."),
        "quote_validity": AnalysisProperty(type="string", description="Quote validity period."),
        "notes": AnalysisProperty(type="string", description="Other factual result details."),
        "honest_leverage_used": AnalysisProperty(type="boolean", description="Whether a saved competing quote was used."),
        "ai_disclosed": AnalysisProperty(type="boolean", description="Whether the assistant disclosed it is AI."),
    }
    return AgentPlatformSettingsRequestModel(
        auth=AuthSettings(enable_auth=True),
        data_collection=data_collection,
        data_collection_scopes={name: "conversation" for name in data_collection},
    )


def _upsert_client_tools(api: Any) -> list[str]:
    tool_ids = []
    for name, definition in CLIENT_TOOL_DEFINITIONS.items():
        request = ToolRequestModel(
            tool_config=ToolRequestModelToolConfig_Client(
                **definition.get("tool_options", {}),
                name=name,
                description=definition["description"],
                expects_response=True,
                response_timeout_secs=10,
                parameters=ObjectJsonSchemaPropertyInput(
                    type="object",
                    required=definition["required"],
                    properties={
                        key: LiteralJsonSchemaProperty(**property_definition)
                        for key, property_definition in definition["properties"].items()
                    },
                ),
            )
        )
        page = api.conversational_ai.tools.list(search=name, page_size=100)
        exact = [
            tool
            for tool in getattr(page, "tools", [])
            if getattr(tool, "id", None)
            and getattr(getattr(tool, "tool_config", None), "type", None) == "client"
            and getattr(getattr(tool, "tool_config", None), "name", None) == name
        ]
        response = (
            api.conversational_ai.tools.update(exact[0].id, request=request)
            if exact
            else api.conversational_ai.tools.create(request=request)
        )
        tool_ids.append(response.id)
    return tool_ids


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
        return dict(cast(dict[str, Any], vars(value)))
    raise RuntimeError("unexpected ElevenLabs agent response")


def _verify_remote_agent(api: Any, agent_id: str, tool_ids: list[str]) -> None:
    remote = _as_dict(api.conversational_ai.agents.get(agent_id))
    if remote.get("agent_id") != agent_id:
        raise RuntimeError("ElevenLabs verification returned a different agent_id")
    conversation = _as_dict(remote.get("conversation_config", {}))
    agent = _as_dict(conversation.get("agent", {}))
    prompt = _as_dict(agent.get("prompt", {}))
    if prompt.get("prompt") != AGENT_NEGOTIATOR_SYSTEM_PROMPT:
        raise RuntimeError("ElevenLabs Agent Negotiator prompt verification failed")
    if set(prompt.get("tool_ids", [])) != set(tool_ids):
        raise RuntimeError("ElevenLabs Agent Negotiator client-tool verification failed")
    built_in_tools = _as_dict(prompt.get("built_in_tools", {}))
    end_call = _as_dict(built_in_tools.get("end_call", {}))
    if end_call.get("name") != "end_call":
        raise RuntimeError("ElevenLabs Agent Negotiator end-call tool verification failed")
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
    tool_ids = _upsert_client_tools(api)
    conversation_config = _conversation_config(config.elevenlabs_agent_negotiator_llm, tool_ids)
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

    _verify_remote_agent(api, agent_id, tool_ids)
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
