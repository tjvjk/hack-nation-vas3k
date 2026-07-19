# The Negotiator orchestrator

Python control plane for the human-in-the-loop moving negotiation demo.

## Local run

The root `.env` must contain `ELEVENLABS_API_KEY`. On every container start,
`create_agents.py` runs before Uvicorn/MCP:

1. reads `elevenlabs_agent_negotiator_id` from SQLite;
2. creates Agent Negotiator from `prompts.py` when the id is absent (or the remote id was deleted);
3. otherwise updates the existing agent with the current prompt and first message;
4. persists the resulting id and prompt hash in SQLite;
5. starts the orchestrator only after synchronization succeeds.

Optional settings:

```dotenv
ELEVENLABS_WEBHOOK_SECRET=optional_webhook_secret
ELEVENLABS_AGENT_NEGOTIATOR_LLM=gpt-4o-mini
```

Run:

```bash
docker compose -f docker-compose.yaml up --build
```

Open <http://localhost:8000>. Provisioning failure is fail-fast: MCP is not exposed with a missing or stale Agent Negotiator configuration.

## External integration endpoints

- Streamable HTTP MCP: `POST /mcp`
- ElevenLabs post-call webhook: `POST /webhooks/elevenlabs`
- Health: `GET /health`
- Agent Negotiator deployment contract: `GET /api/agent_negotiator/config`

The canonical system prompt, first message, and analysis schema live only in `prompts.py`. Configure Agent Negotiator MCP tools with `call_id` and `call_capability` dynamic variables. The carrier widget is a browser demo session; it is not Twilio/SIP/PSTN transport.
