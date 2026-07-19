from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import httpx

from .config import Settings

MOVE_SIZES = {
    0: "studio_apartment",
    1: "one_large_bedroom",
    2: "two_bedrooms",
    3: "three_bedrooms",
    4: "four_bedrooms",
}


class MoveBuddhaClient:
    def __init__(self, settings: Settings):
        self.settings = settings

    async def benchmark(self, move_spec: Mapping[str, Any]) -> dict[str, Any]:
        if not self.settings.movebuddha_api_token:
            return self._unavailable("MOVEBUDDHA_API_TOKEN is not configured")
        try:
            origin_place_id = await self._place_id(move_spec, "origin")
            destination_place_id = await self._place_id(move_spec, "destination")
        except ValueError as exc:
            return self._unavailable(str(exc))
        payload = {
            "origin_place_id": origin_place_id,
            "destination_place_id": destination_place_id,
            "move_size": MOVE_SIZES.get(int(move_spec.get("bedrooms", 2)), "five_bedrooms"),
            "pickup_date": move_spec["move_date"],
        }
        try:
            async with httpx.AsyncClient(timeout=12) as client:
                response = await client.post(
                    self.settings.movebuddha_api_url,
                    json=payload,
                    headers={
                        "Accept": "application/json",
                        "Authorization": f"Bearer {self.settings.movebuddha_api_token}",
                    },
                )
                response.raise_for_status()
        except httpx.HTTPError as exc:
            return self._unavailable(f"moveBuddha estimate request failed: {exc}")
        response_body = response.json()
        estimate = self._professional_estimate(response_body, payload["move_size"])
        if estimate is None:
            return self._unavailable("moveBuddha response did not contain a professional-mover range")
        return {
            "available": True,
            "source": "moveBuddha moving cost calculator",
            "currency": "USD",
            "professional_mover_range": estimate,
            "distance_miles": response_body.get("distance"),
            "usage": "Market benchmark only; it is not a carrier quote or a guarantee.",
        }

    async def _place_id(self, move_spec: Mapping[str, Any], field: str) -> str:
        supplied = move_spec.get(f"{field}_place_id")
        if isinstance(supplied, str) and supplied.strip():
            return supplied
        if not self.settings.google_maps_api_key:
            raise ValueError(f"{field}_place_id or GOOGLE_MAPS_API_KEY is required for a moveBuddha benchmark")
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                "https://maps.googleapis.com/maps/api/geocode/json",
                params={"address": move_spec[field], "key": self.settings.google_maps_api_key},
            )
            response.raise_for_status()
        body = response.json()
        results = body.get("results", [])
        if body.get("status") != "OK" or not results or not results[0].get("place_id"):
            raise ValueError(f"could not resolve {field} to a Google Place ID")
        return results[0]["place_id"]

    @staticmethod
    def _professional_estimate(payload: Any, move_size: str) -> dict[str, float] | None:
        if not isinstance(payload, dict):
            return None
        professional = None
        sizes = payload.get("sizes")
        if isinstance(sizes, dict) and isinstance(sizes.get(move_size), dict):
            professional = sizes[move_size].get("professional")
        if not isinstance(professional, dict):
            professional = payload.get("professional")
        if not isinstance(professional, dict):
            for value in payload.values():
                if isinstance(value, dict) and isinstance(value.get("professional"), dict):
                    professional = value["professional"]
                    break
        if not isinstance(professional, dict):
            return None
        low, high = professional.get("min"), professional.get("max")
        if not isinstance(low, (int, float)) or not isinstance(high, (int, float)) or low < 0 or high < low:
            return None
        return {"low": float(low), "high": float(high)}

    @staticmethod
    def _unavailable(reason: str) -> dict[str, Any]:
        return {
            "available": False,
            "source": "moveBuddha moving cost calculator",
            "reason": reason,
            "usage": "Do not state or imply a market price when this benchmark is unavailable.",
        }
