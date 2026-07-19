#!/usr/bin/env python3
"""Download a small, reproducible FMCSA carrier directory for the demo.

The FMCSA Company Census Socrata endpoint is public and does not require an API key.
"""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

ENDPOINT = "https://data.transportation.gov/resource/az4n-8mr2.json"
FIELDS = "legal_name,phone,phy_city,phy_state,phy_zip,dot_number,status_code,carrier_operation,truck_units"
DEFAULT_OUTPUT = Path(__file__).resolve().parents[1] / "seed" / "fmcsa_carriers.json"


def fetch(state: str, limit: int) -> list[dict]:
    where = f"status_code='A' AND phy_state='{state.upper()}' AND legal_name like '%MOVING%'"
    query = urlencode({"$limit": limit, "$where": where, "$select": FIELDS})
    with urlopen(f"{ENDPOINT}?{query}", timeout=60) as response:
        records = json.load(response)
    return [record for record in records if record.get("phone") and record.get("dot_number")]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state", default="NC", help="two-letter state for active mover records")
    parser.add_argument("--limit", type=int, default=3, help="number of carriers to write")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    records = fetch(args.state, max(args.limit * 10, 20))[: args.limit]
    if len(records) < args.limit:
        raise SystemExit(f"FMCSA returned only {len(records)} usable active carriers")
    for record in records:
        record["source"] = "FMCSA Company Census"
        record["source_url"] = "https://data.transportation.gov/Trucking-and-Motorcoaches/Company-Census-File/az4n-8mr2"
        record["retrieved_at"] = datetime.now(UTC).isoformat()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(records, indent=2) + "\n")
    print(f"Wrote {len(records)} active FMCSA carrier records to {args.output}")


if __name__ == "__main__":
    main()
