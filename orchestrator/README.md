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

## Real company directory

The campaign uses real active carrier directory records from the official FMCSA
Company Census, bundled in `seed/fmcsa_carriers.json`. The counterparties in
the widget remain explicitly simulated; this directory must not be represented
as a real quote or a confirmation that a carrier serves a particular move.

Refresh the directory without an API key:

```bash
python orchestrator/scripts/download_fmcsa_carriers.py
```

The script queries the public FMCSA Socrata endpoint and writes the three
records used by the demo. It does not download or store credentials.
Set `CARRIERS_DATA_FILE` only when overriding the bundled directory (inside the
container its default is `/app/seed/fmcsa_carriers.json`).

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

## TODO

- Parse the large free-text request on the fly into structured move/call data before submitting it to the orchestrator API.
