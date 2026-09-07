from __future__ import annotations
import argparse, json, os
from datetime import datetime
from pathlib import Path
from .models import CapabilityArtifact
from .replay import replay


def main():
    p = argparse.ArgumentParser(prog="computer-use")
    sub = p.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("discover")
    d.add_argument("--goal", required=True); d.add_argument("--url", default="http://127.0.0.1:8000")
    d.add_argument("--artifact", default="artifacts/member_balance.json"); d.add_argument("--headless", action="store_true")
    r = sub.add_parser("replay")
    r.add_argument("--artifact", required=True); r.add_argument("--params", default="{}")
    r.add_argument("--headless", action="store_true"); r.add_argument("--allow-risky", action="store_true")
    args = p.parse_args()
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if args.cmd == "discover":
        from .discovery import discover
        ev = Path("evidence/live") / f"discovery_{stamp}"
        artifact = discover(args.goal, args.url, Path(args.artifact), ev, headless=args.headless)
        print(artifact.model_dump_json(indent=2))
    else:
        artifact = CapabilityArtifact.model_validate_json(Path(args.artifact).read_text())
        params = json.loads(args.params)
        ev = Path("evidence/live") / f"replay_{stamp}"
        result = replay(artifact, params, ev, headless=args.headless, allow_risky=args.allow_risky)
        print(result.model_dump_json(indent=2))
