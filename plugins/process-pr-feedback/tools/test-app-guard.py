#!/usr/bin/env python3
"""Regression tests for app-guard.py. Run: python3 test-app-guard.py"""
import importlib.util
import os
import subprocess
import sys

spec = importlib.util.spec_from_file_location(
    "app_guard", os.path.join(os.path.dirname(os.path.realpath(__file__)), "app-guard.py"))
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)

ME, PEER, DEAD = "me-sid", "peer-sid", "dead-sid"
LIVE = {ME: {"name": "me"}, PEER: {"name": "peer work", "cwd": "/wt/peer", "kind": "bg"}}


def proc(pid, comm, cmdline, sid):
    return {"pid": pid, "comm": comm, "cmdline": cmdline, "sid": sid}


ELECTRON = "/x/node_modules/electron/dist/electron ."
CASES = [
    ("nothing running", [], {}, "CLEAR"),
    ("only my app", [proc(10, "electron", ELECTRON, ME)], {8876: [10]}, "CLEAR"),
    ("leftover of an ended session", [proc(11, "electron", ELECTRON, DEAD)], {8876: [11]}, "CLEAR"),
    ("peer app holds a port", [proc(12, "electron", ELECTRON, PEER)], {8876: [12]}, "WAIT"),
    ("peer e2e runner between launches", [proc(13, "node", "node e2e-tests/run-isolated.mjs x", PEER)], {}, "WAIT"),
    ("peer dotnet test, ports free", [proc(14, "dotnet", "dotnet test c-sharp-tests/", PEER)], {}, "START_ONLY"),
    ("peer webpack build, ports free", [proc(15, "node", "node webpack --config x", PEER)], {}, "START_ONLY"),
    ("human-run app holds a port", [proc(16, "electron", ELECTRON, None)], {1212: [16]}, "ASK"),
    ("editor's dotnet, no port", [proc(17, "dotnet", "dotnet LanguageServer.dll", None)], {}, "START_ONLY"),
    ("port held by an unreadable process", [], {9223: [-1]}, "ASK"),
    ("vitest is excluded like npm stop does", [proc(18, "node", "node vitest run vite.config", PEER)], {}, "CLEAR"),
    ("peer port beats unattributed port", [proc(19, "electron", ELECTRON, PEER), proc(20, "electron", ELECTRON, None)],
     {8876: [19], 1212: [20]}, "WAIT"),
]

failures = 0
for name, processes, ports, expected in CASES:
    got = guard.classify(processes, ports, LIVE, ME)["verdict"]
    ok = got == expected
    failures += not ok
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + ("" if ok else f"  (expected {expected}, got {got})"))

# killable lists only mine and leftovers, never a peer's or an unknown pid
r = guard.classify([proc(10, "electron", ELECTRON, ME), proc(11, "dotnet", "dotnet x", DEAD),
                    proc(12, "electron", ELECTRON, PEER), proc(16, "electron", ELECTRON, None)], {}, LIVE, ME)
ok = sorted(r["killable"]) == [10, 11] and [p["name"] for p in r["peers"]] == ["peer work"]
failures += not ok
print(f"{'PASS' if ok else 'FAIL'}  killable = mine + leftovers only; peer named" + ("" if ok else f"  got {r}"))

# the npm shim no-ops `npm stop` and forwards everything else to the real npm
shim_dir = "/home/paratext/.claude/tools/npm-no-stop"
env = {**os.environ, "PATH": f"{shim_dir}:{os.environ['PATH']}"}
stop = subprocess.run(["npm", "stop"], env=env, capture_output=True, text=True)
ver = subprocess.run(["npm", "--version"], env=env, capture_output=True, text=True)
ok = stop.returncode == 0 and "skipped" in stop.stdout and ver.returncode == 0 and ver.stdout.strip()[:1].isdigit()
failures += not ok
print(f"{'PASS' if ok else 'FAIL'}  npm shim: stop skipped, other commands forwarded"
      + ("" if ok else f"  stop={stop.stdout!r}{stop.stderr!r} ver={ver.stdout!r}{ver.stderr!r}"))

total = len(CASES) + 2
print(f"\n{total - failures}/{total} passed")
sys.exit(1 if failures else 0)
