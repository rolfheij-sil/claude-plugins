#!/usr/bin/env python3
"""Decide whether this session may start the paranext-core dev app without hurting another session.

`./.erb/scripts/refresh.sh` begins with `npm stop`, which kills machine-wide, by name: every
`electron` and every `dotnet` process, and every process whose command line contains `electronmon`,
`esbuild`, `nodemon`, `vite`, `webpack` or `extension-host` (paranext-core `stop-processes.mjs`).
That takes out other sessions' apps, e2e runs, `dotnet test` runs and builds. The app's ports
(8876 PAPI, 1212 renderer, 9223/9222 CDP) are machine-wide too.

Ownership is exact rather than guessed from folders: every command a Claude session runs carries
CLAUDE_CODE_SESSION_ID in its environment and its children inherit it, so /proc/<pid>/environ names
the session that started a process. A session is live when ~/.claude/sessions/<pid>.json exists,
that pid is running, and its kernel start time equals the file's `procStart` (guards pid reuse).

Each relevant process is one of: mine (this session), peer (a live other session), leftover (a
session that has ended), or unattributed (no session id: a human terminal, an editor, the system).

Verdict, also the exit status:
  0 CLEAR       nothing `npm stop` would kill belongs to a peer or to nobody-we-know; run refresh.sh.
  3 START_ONLY  the ports are free (or held only by mine/leftovers), but `npm stop` would kill
                someone else's processes: start the app with `npm stop` skipped (see --no-stop-path).
  4 WAIT        a live peer holds an app port or is running e2e: coordinate with it, then re-check.
  5 ASK         a process no live session owns holds an app port: the user decides.
Leftovers and mine may be killed by pid; the report prints the exact `kill` line.

Usage: app-guard.py [--json]        report and exit with the verdict
       app-guard.py --no-stop-path  print the PATH prefix that makes `npm stop` a no-op
Tests: python3 test-app-guard.py (beside this file)
"""
import json
import os
import re
import subprocess
import sys

SESSIONS_DIR = os.path.expanduser("~/.claude/sessions")
SELF_PATH = os.path.realpath(__file__)
NO_STOP_DIR = os.path.join(os.path.dirname(SELF_PATH), "npm-no-stop")
APP_PORTS = (8876, 1212, 9223, 9222)
# Mirrors paranext-core stop-processes.mjs: name kills plus command-line search terms.
KILLED_BY_NAME = ("electron", "dotnet")
SEARCH_TERMS = ("electronmon", "esbuild", "nodemon", "vite", "webpack", "extension-host")
EXCLUDED_PATHS = ("vitest", "/scripture-editors/node_modules/")
# An e2e runner between Electron launches holds no port, but starting an app then breaks its next launch.
E2E_RUNNER = re.compile(r"playwright|run-isolated\.mjs|run-e2e-wsl\.sh")

VERDICT_EXIT = {"CLEAR": 0, "START_ONLY": 3, "WAIT": 4, "ASK": 5}


def killed_by_npm_stop(comm: str, cmdline: str) -> bool:
    if comm in KILLED_BY_NAME:
        return True
    return any(t in cmdline for t in SEARCH_TERMS) and not any(p in cmdline for p in EXCLUDED_PATHS)


def classify(processes: list[dict], port_holders: dict[int, list[int]], live: dict[str, dict],
             self_sid: str) -> dict:
    """Pure decision logic. processes: {pid, comm, cmdline, sid}; port_holders: port -> pids;
    live: session id -> registry entry for live sessions."""
    by_pid = {p["pid"]: p for p in processes}

    def owner(p: dict) -> str:
        sid = p.get("sid")
        if not sid:
            return "unattributed"
        if sid == self_sid:
            return "mine"
        return "peer" if sid in live else "leftover"

    relevant: dict[int, dict] = {}
    for p in processes:
        reasons = []
        if killed_by_npm_stop(p["comm"], p["cmdline"]):
            reasons.append("npm stop kills it")
        if E2E_RUNNER.search(p["cmdline"]):
            reasons.append("e2e runner")
        if reasons:
            relevant[p["pid"]] = {**p, "owner": owner(p), "reasons": reasons}
    for port, pids in port_holders.items():
        for pid in pids:
            p = by_pid.get(pid, {"pid": pid, "comm": "?", "cmdline": "?", "sid": None})
            entry = relevant.setdefault(pid, {**p, "owner": owner(p), "reasons": []})
            entry["reasons"].append(f"holds port {port}")

    def holds_port(e: dict) -> bool:
        return any(r.startswith("holds port") for r in e["reasons"])

    entries = sorted(relevant.values(), key=lambda e: e["pid"])
    foreign = [e for e in entries if e["owner"] in ("peer", "unattributed")]
    if any(e["owner"] == "peer" and (holds_port(e) or "e2e runner" in e["reasons"]) for e in entries):
        verdict = "WAIT"
    elif any(e["owner"] == "unattributed" and holds_port(e) for e in entries):
        verdict = "ASK"
    elif foreign:
        verdict = "START_ONLY"
    else:
        verdict = "CLEAR"

    peers = {}
    for e in entries:
        if e["owner"] == "peer":
            s = live[e["sid"]]
            peers.setdefault(e["sid"], {"session_id": e["sid"], "name": s.get("name"), "cwd": s.get("cwd"),
                                        "kind": s.get("kind"), "pids": []})["pids"].append(e["pid"])
    killable = [e["pid"] for e in entries if e["owner"] in ("mine", "leftover")]
    return {"verdict": verdict, "processes": entries, "peers": list(peers.values()), "killable": killable}


# ---------------------------------------------------------------- live system readers


def _read(path: str, binary: bool = False):
    try:
        with open(path, "rb" if binary else "r") as f:
            return f.read()
    except OSError:
        return None


def start_time(pid: int) -> str | None:
    stat = _read(f"/proc/{pid}/stat")
    if not stat:
        return None
    # Field 22; the command name (field 2) may contain spaces, so split after its closing paren.
    return stat[stat.rindex(")") + 2:].split()[19]


def live_sessions() -> dict[str, dict]:
    live = {}
    for name in os.listdir(SESSIONS_DIR) if os.path.isdir(SESSIONS_DIR) else []:
        if not name.endswith(".json"):
            continue
        try:
            entry = json.loads(_read(os.path.join(SESSIONS_DIR, name)) or "")
        except ValueError:
            continue
        pid, sid = entry.get("pid"), entry.get("sessionId")
        if pid and sid and start_time(int(pid)) == str(entry.get("procStart")):
            live[sid] = entry
    return live


def snapshot_processes() -> list[dict]:
    me = os.getpid()
    out = []
    for name in os.listdir("/proc"):
        if not name.isdigit() or int(name) == me:
            continue
        pid = int(name)
        raw = _read(f"/proc/{pid}/cmdline", binary=True)
        comm = (_read(f"/proc/{pid}/comm") or "").strip()
        if raw is None or not comm:
            continue
        env = _read(f"/proc/{pid}/environ", binary=True) or b""
        sid = None
        for item in env.split(b"\0"):
            if item.startswith(b"CLAUDE_CODE_SESSION_ID="):
                sid = item.split(b"=", 1)[1].decode(errors="replace")
                break
        out.append({"pid": pid, "comm": comm, "cmdline": raw.replace(b"\0", b" ").decode(errors="replace").strip(),
                    "sid": sid})
    return out


def snapshot_ports() -> dict[int, list[int]]:
    try:
        text = subprocess.run(["ss", "-ltnpH"], capture_output=True, text=True, timeout=10).stdout
    except (OSError, subprocess.SubprocessError):
        return {}
    holders: dict[int, list[int]] = {}
    for line in text.splitlines():
        cols = line.split()
        if len(cols) < 4:
            continue
        port = cols[3].rsplit(":", 1)[-1]
        if port.isdigit() and int(port) in APP_PORTS:
            pids = [int(p) for p in re.findall(r"pid=(\d+)", line)]
            # ss shows no pid for another user's socket; record the port as held regardless.
            holders.setdefault(int(port), []).extend(pids or [-1])
    return holders


def report(result: dict) -> str:
    lines = [f"VERDICT: {result['verdict']}"]
    for e in result["processes"]:
        lines.append(f"  {e['owner']:<12} pid {e['pid']:<7} {e['comm']:<14} {', '.join(e['reasons'])} :: "
                     f"{e['cmdline'][:110]}")
    for s in result["peers"]:
        lines.append(f"  peer session: name={s['name']!r} id={s['session_id']} kind={s['kind']} cwd={s['cwd']} "
                     f"pids={s['pids']}")
    if result["killable"]:
        lines.append(f"  mine/leftover, safe to stop by pid: kill {' '.join(map(str, result['killable']))}")
    no_stop_start = (f"PATH=\"$(python3 '{SELF_PATH}' --no-stop-path):$PATH\" "
                     "<worktree>/.erb/scripts/refresh.sh")
    advice = {
        "CLEAR": "Nothing of anyone else's is in the way. Start without npm stop: " + no_stop_start
                 + " — and if the app gets stuck, plain refresh.sh (with npm stop) is safe right now.",
        "START_ONLY": "Ports are free; start without npm stop: " + no_stop_start + " — but do NOT run npm stop "
                      "or plain refresh.sh: it would kill the processes listed above. If stuck, clear it with "
                      "their owners (or the user) first.",
        "WAIT": "A live peer is using the app or running e2e: message it, wait, re-check. Never kill it.",
        "ASK": "A process no live session owns holds an app port (a manual run, an editor, or a leftover "
               "without a session id): ask the user.",
    }
    lines.append(advice[result["verdict"]])
    return "\n".join(lines)


def main() -> None:
    if "--no-stop-path" in sys.argv:
        print(NO_STOP_DIR)
        return
    self_sid = os.environ.get("CLAUDE_CODE_SESSION_ID", "")
    result = classify(snapshot_processes(), snapshot_ports(), live_sessions(), self_sid)
    print(json.dumps(result, indent=2) if "--json" in sys.argv else report(result))
    sys.exit(VERDICT_EXIT[result["verdict"]])


if __name__ == "__main__":
    main()
