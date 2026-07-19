from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path
import secrets
import sqlite3
import threading
from typing import Any
import uuid

PERSONAS = [
    {
        "carrier_id": "metro-tough",
        "carrier_name": "Metro Tough Movers",
        "style": "tough_negotiator",
        "headline": "Tough negotiator",
        "private_brief": "Start at $2,450. Your floor is $2,050. Concede only after a concrete benchmark or a verified competing quote.",
    },
    {
        "carrier_id": "budget-hidden",
        "carrier_name": "Budget Hidden Fee Moving",
        "style": "hidden_fee_lowballer",
        "headline": "Hidden-fee lowballer",
        "private_brief": "Quote $1,100, then add $350 stairs, $250 fuel, and $300 long-carry fees. Resist itemizing until pressed.",
    },
    {
        "carrier_id": "premium-stonewall",
        "carrier_name": "Premium Hard Sell Logistics",
        "style": "hard_sell_stonewaller",
        "headline": "Hard sell / stonewall",
        "private_brief": "Start at $2,300 and demand a deposit. Your floor is $1,900, or offer free packing when shown strong verified leverage.",
    },
]

TERMINAL_STATUSES = {"completed", "declined", "failed", "no_answer"}


def _now() -> str:
    return datetime.now(UTC).isoformat()


class Store:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._init_schema()

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        return connection

    def _init_schema(self) -> None:
        with self.connect() as db:
            db.executescript(
                """
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS moves (
                    id TEXT PRIMARY KEY,
                    spec_json TEXT NOT NULL,
                    consent_json TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS campaigns (
                    id TEXT PRIMARY KEY,
                    move_id TEXT NOT NULL UNIQUE REFERENCES moves(id),
                    status TEXT NOT NULL,
                    benchmark_low REAL NOT NULL,
                    benchmark_high REAL NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS call_jobs (
                    id TEXT PRIMARY KEY,
                    campaign_id TEXT NOT NULL REFERENCES campaigns(id),
                    sequence_no INTEGER NOT NULL,
                    carrier_json TEXT NOT NULL,
                    status TEXT NOT NULL,
                    capability TEXT NOT NULL,
                    conversation_id TEXT UNIQUE,
                    progress_json TEXT,
                    result_json TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(campaign_id, sequence_no)
                );
                CREATE TABLE IF NOT EXISTS webhook_events (
                    event_key TEXT PRIMARY KEY,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS runtime_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                """
            )

    def reset(self) -> None:
        with self._lock, self.connect() as db:
            db.executescript("DELETE FROM webhook_events; DELETE FROM call_jobs; DELETE FROM campaigns; DELETE FROM moves;")

    def get_setting(self, key: str) -> str | None:
        with self.connect() as db:
            row = db.execute("SELECT value FROM runtime_settings WHERE key=?", (key,)).fetchone()
        return row["value"] if row else None

    def set_setting(self, key: str, value: str) -> None:
        with self.connect() as db:
            db.execute(
                """INSERT INTO runtime_settings(key, value, updated_at) VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at""",
                (key, value, _now()),
            )

    def create_move(self, spec: dict[str, Any]) -> dict[str, Any]:
        move_id = str(uuid.uuid4())
        consent = {
            "granted": True,
            "granted_at": _now(),
            "max_carriers": spec["max_carriers"],
            "channel": "browser_demo",
        }
        clean_spec = {key: value for key, value in spec.items() if key not in {"confirmed", "outreach_consent"}}
        with self.connect() as db:
            db.execute(
                "INSERT INTO moves VALUES (?, ?, ?, 'confirmed', ?)",
                (move_id, json.dumps(clean_spec), json.dumps(consent), _now()),
            )
        return {"id": move_id, "status": "confirmed", "spec": clean_spec, "consent": consent}

    def start_campaign(self, move_id: str) -> dict[str, Any]:
        with self._lock, self.connect() as db:
            existing = db.execute("SELECT id FROM campaigns WHERE move_id=?", (move_id,)).fetchone()
            if existing:
                return self.get_campaign(existing["id"])
            move = db.execute("SELECT * FROM moves WHERE id=?", (move_id,)).fetchone()
            if not move:
                raise KeyError("move not found")
            consent = json.loads(move["consent_json"])
            if move["status"] != "confirmed" or not consent.get("granted"):
                raise ValueError("confirmed move and active consent are required")
            spec = json.loads(move["spec_json"])
            baseline = max(float(spec["budget_min"] or 1500), 1000)
            benchmark_low = round(baseline * 0.9, 2)
            benchmark_high = round(max(float(spec["budget_max"]), benchmark_low * 1.35), 2)
            campaign_id = str(uuid.uuid4())
            now = _now()
            db.execute(
                "INSERT INTO campaigns VALUES (?, ?, 'calling', ?, ?, ?, ?)",
                (campaign_id, move_id, benchmark_low, benchmark_high, now, now),
            )
            for index, persona in enumerate(PERSONAS[: consent["max_carriers"]]):
                status = "offered_to_widget" if index == 0 else "scheduled"
                db.execute(
                    "INSERT INTO call_jobs VALUES (?, ?, ?, ?, ?, ?, NULL, NULL, NULL, ?, ?)",
                    (
                        str(uuid.uuid4()),
                        campaign_id,
                        index + 1,
                        json.dumps(persona),
                        status,
                        secrets.token_urlsafe(32),
                        now,
                        now,
                    ),
                )
        return self.get_campaign(campaign_id)

    def get_campaign(self, campaign_id: str) -> dict[str, Any]:
        with self.connect() as db:
            campaign = db.execute("SELECT * FROM campaigns WHERE id=?", (campaign_id,)).fetchone()
            if not campaign:
                raise KeyError("campaign not found")
            move = db.execute("SELECT * FROM moves WHERE id=?", (campaign["move_id"],)).fetchone()
            jobs = db.execute("SELECT * FROM call_jobs WHERE campaign_id=? ORDER BY sequence_no", (campaign_id,)).fetchall()
        return self._campaign_dict(campaign, move, jobs)

    def snapshot(self) -> dict[str, Any]:
        with self.connect() as db:
            rows = db.execute("SELECT id FROM campaigns ORDER BY created_at DESC").fetchall()
        return {"campaigns": [self.get_campaign(row["id"]) for row in rows]}

    def _campaign_dict(self, campaign: sqlite3.Row, move: sqlite3.Row, jobs: list[sqlite3.Row]) -> dict[str, Any]:
        public_jobs = []
        for row in jobs:
            result = json.loads(row["result_json"]) if row["result_json"] else None
            public_jobs.append(
                {
                    "id": row["id"],
                    "sequence_no": row["sequence_no"],
                    "carrier": json.loads(row["carrier_json"]),
                    "status": row["status"],
                    "conversation_id": row["conversation_id"],
                    "result": result,
                }
            )
        return {
            "id": campaign["id"],
            "move_id": campaign["move_id"],
            "status": campaign["status"],
            "benchmark": {"low": campaign["benchmark_low"], "high": campaign["benchmark_high"], "currency": "USD"},
            "move": json.loads(move["spec_json"]),
            "jobs": public_jobs,
            "ranking": self._rank(public_jobs, float(campaign["benchmark_low"])),
        }

    @staticmethod
    def _rank(jobs: list[dict[str, Any]], benchmark_low: float) -> list[dict[str, Any]]:
        ranked = []
        for job in jobs:
            result = job.get("result") or {}
            if result.get("outcome") != "itemized_quote" or result.get("final_total") is None:
                continue
            red_flags = list(result.get("red_flags", []))
            total = float(result["final_total"])
            ranked.append(
                {
                    "call_id": job["id"],
                    "carrier_name": job["carrier"]["carrier_name"],
                    "final_total": total,
                    "red_flags": red_flags,
                    "recommended": False,
                }
            )
        ranked.sort(key=lambda item: ("suspicious_lowball" in item["red_flags"], item["final_total"]))
        safe = next((item for item in ranked if "suspicious_lowball" not in item["red_flags"]), None)
        if safe:
            safe["recommended"] = True
        return ranked

    def _job_with_context(self, db: sqlite3.Connection, call_id: str) -> tuple[sqlite3.Row, sqlite3.Row, sqlite3.Row]:
        job = db.execute("SELECT * FROM call_jobs WHERE id=?", (call_id,)).fetchone()
        if not job:
            raise KeyError("call not found")
        campaign = db.execute("SELECT * FROM campaigns WHERE id=?", (job["campaign_id"],)).fetchone()
        move = db.execute("SELECT * FROM moves WHERE id=?", (campaign["move_id"],)).fetchone()
        return job, campaign, move

    def answer_call(self, call_id: str) -> dict[str, Any]:
        with self._lock, self.connect() as db:
            changed = db.execute(
                "UPDATE call_jobs SET status='in_progress', updated_at=? WHERE id=? AND status='offered_to_widget'",
                (_now(), call_id),
            ).rowcount
            if changed != 1:
                raise ValueError("call is not available to answer")
            job, _, _ = self._job_with_context(db, call_id)
        return {"id": job["id"], "status": "in_progress"}

    def call_context(self, call_id: str, capability: str | None = None) -> dict[str, Any]:
        with self.connect() as db:
            job, campaign, move = self._job_with_context(db, call_id)
            if capability is not None and not secrets.compare_digest(job["capability"], capability):
                raise PermissionError("invalid call capability")
            previous = db.execute(
                "SELECT result_json FROM call_jobs WHERE campaign_id=? AND sequence_no<? AND result_json IS NOT NULL ORDER BY sequence_no",
                (campaign["id"], job["sequence_no"]),
            ).fetchall()
        verified_quotes = []
        for row in previous:
            result = json.loads(row["result_json"])
            if result.get("outcome") == "itemized_quote" and result.get("final_total") is not None:
                verified_quotes.append({"final_total": result["final_total"], "currency": "USD"})
        return {
            "call_id": call_id,
            "move_spec": json.loads(move["spec_json"]),
            "carrier": json.loads(job["carrier_json"]),
            "benchmark": {"low": campaign["benchmark_low"], "high": campaign["benchmark_high"], "currency": "USD"},
            "verified_quotes": verified_quotes,
            "honesty_rules": ["Disclose that you are an AI assistant", "Never invent inventory or competing offers", "Do not book or pay a deposit"],
        }

    def session_variables(self, call_id: str) -> dict[str, Any]:
        with self.connect() as db:
            job, _, _ = self._job_with_context(db, call_id)
            if job["status"] != "in_progress":
                raise ValueError("call must be answered first")
        return {"call_id": call_id, "call_capability": job["capability"]}

    def record_started(self, call_id: str, capability: str, conversation_id: str) -> dict[str, Any]:
        self.call_context(call_id, capability)
        with self.connect() as db:
            db.execute(
                "UPDATE call_jobs SET conversation_id=COALESCE(conversation_id, ?), updated_at=? WHERE id=?",
                (conversation_id, _now(), call_id),
            )
        return {"ok": True, "call_id": call_id, "conversation_id": conversation_id}

    def save_progress(self, call_id: str, capability: str, progress: dict[str, Any]) -> dict[str, Any]:
        self.call_context(call_id, capability)
        with self.connect() as db:
            db.execute("UPDATE call_jobs SET progress_json=?, updated_at=? WHERE id=?", (json.dumps(progress), _now(), call_id))
        return {"ok": True}

    def finish_call(self, call_id: str, result: dict[str, Any], capability: str | None = None) -> dict[str, Any]:
        with self._lock, self.connect() as db:
            job, campaign, _ = self._job_with_context(db, call_id)
            if capability is not None and not secrets.compare_digest(job["capability"], capability):
                raise PermissionError("invalid call capability")
            if job["status"] in TERMINAL_STATUSES:
                return {"id": call_id, "status": job["status"], "idempotent": True}
            outcome = result["outcome"]
            status = "completed" if outcome == "itemized_quote" else ("declined" if outcome == "documented_decline" else "failed")
            red_flags = list(result.get("red_flags", []))
            if result.get("final_total") is not None and float(result["final_total"]) < float(campaign["benchmark_low"]) * 0.7:
                red_flags.append("suspicious_lowball")
            result["red_flags"] = sorted(set(red_flags))
            db.execute(
                "UPDATE call_jobs SET status=?, result_json=?, conversation_id=COALESCE(conversation_id, ?), updated_at=? WHERE id=?",
                (status, json.dumps(result), result.get("conversation_id"), _now(), call_id),
            )
            next_job = db.execute(
                "SELECT id FROM call_jobs WHERE campaign_id=? AND status='scheduled' ORDER BY sequence_no LIMIT 1",
                (campaign["id"],),
            ).fetchone()
            if next_job:
                db.execute("UPDATE call_jobs SET status='offered_to_widget', updated_at=? WHERE id=?", (_now(), next_job["id"]))
            else:
                unfinished = db.execute(
                    "SELECT COUNT(*) AS n FROM call_jobs WHERE campaign_id=? AND status NOT IN ('completed','declined','failed','no_answer')",
                    (campaign["id"],),
                ).fetchone()["n"]
                if unfinished == 0:
                    db.execute("UPDATE campaigns SET status='completed', updated_at=? WHERE id=?", (_now(), campaign["id"]))
        return {"id": call_id, "status": status, "idempotent": False}

    def store_webhook(self, event_key: str, payload: dict[str, Any]) -> bool:
        with self.connect() as db:
            return (
                db.execute(
                    "INSERT OR IGNORE INTO webhook_events VALUES (?, ?, ?)",
                    (event_key, json.dumps(payload), _now()),
                ).rowcount
                == 1
            )
