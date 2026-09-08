#!/usr/bin/env python3
"""Poll mempool's liquid.network Esplora for the state of the valid chain and
whether any fork transactions have been replayed above the halt height. stdlib
only. Writes monitor/status.json and appends monitor/tips-history.csv ONLY when
something changes, so commit history stays clean. Exit 10 = changed."""
import csv, json, socket, sys, urllib.request
from datetime import datetime, timezone
from pathlib import Path
REPO = Path(__file__).resolve().parent.parent
BASE = "https://liquid.network/api"
HALT = 4050335
FORK_336 = "e1d9a2aae69e0fc3ca18f7f7f84e0615e92a5e3b5000d66c10c34043346da0d5"  # fork's block 4,050,336
_g = socket.getaddrinfo
socket.getaddrinfo = lambda *a, **k: sorted(_g(*a, **k), key=lambda ai: ai[0] != socket.AF_INET)
def get(path):
    req = urllib.request.Request(f"{BASE}{path}", headers={"User-Agent": "liquid-replay-monitor"})
    return urllib.request.urlopen(req, timeout=30).read().decode().strip()
def load_set(name):
    p = REPO / name
    return {r["txid"] for r in csv.DictReader(p.open())} if p.exists() else set()
def now(): return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
def main():
    expected = load_set("expected-replay.csv"); tainted = load_set("do-not-expect-replay.csv")
    st_path = REPO / "monitor" / "status.json"
    st = json.loads(st_path.read_text()) if st_path.exists() else {"scanned_through": HALT, "replayed": {}}
    try:
        tip = int(get("/blocks/tip/height")); tip_hash = get(f"/block-height/{tip}")
        h336 = get(f"/block-height/{4050336}") if tip >= 4050336 else None
    except Exception as e:
        print("liquid.network unreachable:", e); return 0
    on_fork = (h336 == FORK_336)
    # replay scan only on a recovery chain (advanced past halt and NOT the fork)
    newly = 0
    if tip > HALT and not on_fork:
        start = max(st.get("scanned_through", HALT), HALT) + 1
        for h in range(start, tip + 1):
            try:
                bh = get(f"/block-height/{h}"); txids = json.loads(get(f"/block/{bh}/txids"))
            except Exception as e:
                st["scan_error"] = f"stopped at {h}: {str(e)[:100]}"; break
            for txid in txids:
                if (txid in expected or txid in tainted) and txid not in st["replayed"]:
                    st["replayed"][txid] = h; newly += 1
            st["scanned_through"] = h; st.pop("scan_error", None)
    rc = {"expected": 0, "tainted": 0}
    for txid in st["replayed"]:
        rc["tainted" if txid in tainted else "expected"] += 1
    prev = {k: st.get(k) for k in ("tip_height", "tip_hash", "block_4050336_hash", "replayed_count", "on_fork")}
    st.update({"tip_height": tip, "tip_hash": tip_hash, "block_4050336_hash": h336, "on_fork": on_fork,
               "halt_height": HALT, "grown_past_halt": max(0, tip - HALT),
               "replayed_count": len(st["replayed"]), "replayed_by_set": rc,
               "expected_total": len(expected), "tainted_total": len(tainted),
               "tainted_replayed_ALERT": rc["tainted"] > 0, "fork_adopted_ALERT": on_fork})
    cur = {k: st.get(k) for k in ("tip_height", "tip_hash", "block_4050336_hash", "replayed_count", "on_fork")}
    changed = cur != prev
    if changed:
        st["last_change_at"] = now()
        st_path.write_text(json.dumps(st, indent=1) + "\n")
        hp = REPO / "monitor" / "tips-history.csv"; new = not hp.exists()
        with hp.open("a", newline="") as f:
            w = csv.writer(f)
            if new: w.writerow(["utc", "tip_height", "tip_hash", "block_4050336_hash", "on_fork", "replayed_count"])
            w.writerow([now(), tip, tip_hash, h336 or "", on_fork, len(st["replayed"])])
        print(f"CHANGED tip={tip} on_fork={on_fork} replayed={len(st['replayed'])} (+{newly})")
        return
    print(f"no change: tip={tip} on_fork={on_fork} replayed={len(st['replayed'])}")
if __name__ == "__main__": main()
