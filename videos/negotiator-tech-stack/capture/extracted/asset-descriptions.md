# Asset inventory

- `repo-ui`: No live browser capture was possible because `http://localhost:8000` was not serving and browser automation could not start. The UI is represented as a stylized, source-grounded interface card rather than a screenshot.
- `compose`: `docker-compose.yaml` defines one `orchestrator` service, publishes port 8000, uses a persistent `negotiator-data` volume, and passes runtime environment configuration.
- `backend`: `orchestrator/app/main.py` creates a Starlette app plus FastMCP streamable HTTP endpoint at `/mcp`.
- `frontend`: `orchestrator/static/app.js` imports `Conversation` from the ElevenLabs browser client and manages the call widget, forms, and structured result rendering.
- `elevenlabs`: `create_agents.py` provisions or updates Agent Negotiator; `elevenlabs_client.py` obtains signed conversation URLs and verifies webhooks.
- `movebuddha`: `orchestrator/app/movebuddha.py` obtains a professional-mover benchmark from moveBuddha.
- `google-maps`: `MoveBuddhaClient._place_id` uses Google Maps Geocoding API server-side when Place IDs are not already supplied.
