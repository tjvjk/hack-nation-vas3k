from __future__ import annotations

import httpx

from .config import Settings


class ElevenLabsGateway:
    def __init__(self, settings: Settings):
        self.settings = settings

    async def get_signed_url(self, agent_id: str | None) -> str | None:
        if not self.settings.elevenlabs_api_key or not agent_id:
            return None
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                "https://api.elevenlabs.io/v1/convai/conversation/get-signed-url",
                params={"agent_id": agent_id},
                headers={"xi-api-key": self.settings.elevenlabs_api_key},
            )
            response.raise_for_status()
            return response.json()["signed_url"]


def verify_webhook(raw_body: bytes, signature: str | None, secret: str) -> dict:
    if not secret:
        import json

        return json.loads(raw_body)
    if not signature:
        raise ValueError("missing ElevenLabs-Signature")
    from elevenlabs import webhooks

    return webhooks.construct_event(rawBody=raw_body.decode("utf-8"), sig_header=signature, secret=secret)
