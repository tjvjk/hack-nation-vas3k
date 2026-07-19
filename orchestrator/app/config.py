from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    data_dir: Path
    database_path: Path
    static_dir: Path
    elevenlabs_api_key: str
    elevenlabs_agent_negotiator_llm: str
    elevenlabs_webhook_secret: str
    public_base_url: str
    call_transport: str
    carrier_data_path: Path
    movebuddha_api_url: str
    movebuddha_api_token: str
    google_maps_api_key: str

    @property
    def live_agent_enabled(self) -> bool:
        return bool(self.elevenlabs_api_key)


def load_settings() -> Settings:
    package_root = Path(__file__).resolve().parent.parent
    data_dir = Path(os.getenv("ORCHESTRATOR_DATA_DIR", package_root / "data"))
    database_url = os.getenv("DATABASE_URL", "")
    if database_url.startswith("sqlite:///"):
        database_path = Path(database_url.removeprefix("sqlite:///"))
    elif database_url.startswith("file:"):
        database_path = Path(database_url.removeprefix("file:"))
    else:
        database_path = data_dir / "negotiator.db"
    return Settings(
        data_dir=data_dir,
        database_path=database_path,
        static_dir=package_root / "static",
        elevenlabs_api_key=os.getenv("ELEVENLABS_API_KEY", ""),
        elevenlabs_agent_negotiator_llm=os.getenv("ELEVENLABS_AGENT_NEGOTIATOR_LLM", "gpt-5.2"),
        elevenlabs_webhook_secret=os.getenv("ELEVENLABS_WEBHOOK_SECRET", ""),
        public_base_url=os.getenv("PUBLIC_BASE_URL", "http://localhost:8000"),
        call_transport=os.getenv("CALL_TRANSPORT", "widget"),
        carrier_data_path=Path(
            os.getenv("CARRIERS_DATA_FILE", package_root / "seed" / "fmcsa_carriers.json")
        ),
        movebuddha_api_url=os.getenv("MOVEBUDDHA_API_URL", "https://api.movebuddha.com/api/v1/estimates"),
        movebuddha_api_token=os.getenv("MOVEBUDDHA_API_TOKEN", ""),
        google_maps_api_key=os.getenv("GOOGLE_MAPS_API_KEY", ""),
    )


settings = load_settings()
