#!/usr/bin/env python3
"""Pull drill tracking sessions from Netlify Blobs into data/tracking.jsonl.

Each stored blob is one batch {drill, session, received, ua, events}. This
lists the drill-tracking store via netlify-cli, downloads every key, and
writes one JSON object per line for estimator.py.

Usage (from anywhere; runs netlify-cli in the site repo):
  python pull_tracking.py [--store drill-tracking] [--out data/tracking.jsonl]
"""

import argparse
import json
import re
import subprocess
from pathlib import Path

SITE_DIR = Path(__file__).resolve().parents[2]   # the harlananelson repo


def sh(args):
    return subprocess.run(args, cwd=SITE_DIR, capture_output=True,
                          text=True, check=False)


def list_keys(store):
    r = sh(["npx", "netlify-cli", "blobs:list", store])
    keys = re.findall(r"^\|\s*(\S+/\S+)\s*\|", r.stdout, re.M)
    return [k for k in keys if k.lower() != "key"]


def get_blob(store, key):
    r = sh(["npx", "netlify-cli", "blobs:get", store, key])
    if r.returncode != 0:
        print(f"  ! failed {key}: {r.stderr.strip()[:120]}")
        return None
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        print(f"  ! unparseable {key}")
        return None


def main():
    ap = argparse.ArgumentParser()
    here = Path(__file__).parent
    ap.add_argument("--store", default="drill-tracking")
    ap.add_argument("--out", default=str(here / "data/tracking.jsonl"))
    args = ap.parse_args()

    keys = list_keys(args.store)
    print(f"{len(keys)} batches in store '{args.store}'")
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with out.open("w") as f:
        for k in keys:
            blob = get_blob(args.store, k)
            if blob is not None:
                f.write(json.dumps(blob, ensure_ascii=False) + "\n")
                n += 1
    print(f"wrote {n} batches -> {out}")


if __name__ == "__main__":
    main()
