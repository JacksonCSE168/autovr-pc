"""Exercise the delivered AutoVR-PC CLI and cross-check the game's independent Player.log."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parent
MARKER = re.compile(r"^SWITCHROOM\|([a-z]+)\|(open|closed)\|(\d+)\s*$", re.MULTILINE)
EXPECTED = [
    ("ready", "closed", "0"), ("shared", "closed", "0"), ("open", "open", "0"),
    ("shared", "open", "0"), ("close", "closed", "0"),
    ("shared", "closed", "0"), ("open", "open", "0"), ("collect", "closed", "1"),
]


def check(condition, message):
    if not condition:
        raise RuntimeError(message)


def wait_for_log(log, player, expected, timeout):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        rows = MARKER.findall(log.read_text(encoding="utf-8", errors="replace")) if log.exists() else []
        check(rows == expected[:len(rows)], f"Unexpected callbacks or state: {rows}, expected {expected}")
        if rows == expected:
            return
        check(player.poll() is None, "Game exited. See Player.log.")
        time.sleep(.1)
    raise RuntimeError(f"Timed out awaiting {expected}; see Player.log.")


def invoke(pid, folder, step, event=None):
    cmd = [sys.executable, str(ROOT / "tool/AutoVR-PC/pc.py"), "--pid", str(pid),
           "--out", str(folder / (step + ".jsonl"))]
    if event is not None:
        cmd.append("--event=" + event)
    result = subprocess.run(cmd, text=True, capture_output=True, errors="replace", timeout=100)
    (folder / (step + ".txt")).write_text(result.stdout + "\n" + result.stderr, encoding="utf-8")
    check(result.returncode == 0, f"AutoVR-PC failed at {step}: {result.stdout[:2000]} {result.stderr[:500]}")
    records = [json.loads(line) for line in (folder / (step + ".jsonl")).read_text().splitlines()]
    if event is not None:
        confirms = [r for r in records if r["type"] == "result"]
        check(len(confirms) == 1 and confirms[0].get("id") == event and confirms[0].get("status") == "Invoke returned",
              f"Missing invocation acknowledgement at {step}")
    return next(r for r in reversed(records) if r["type"] == "scan")


def buttons(scan, opened):
    rows = [r for r in scan["events"] if r["component"] == "Button" and r["field"] == "m_OnClick"]
    found = {r["object"]: r for r in rows}
    expected = {"ButtonA", "ButtonB"} | ({"CollectCore"} if opened else set())
    check(len(rows) == len(expected) and set(found) == expected, f"Unexpected active buttons: {list(found)}")
    check(len({r["id"] for r in rows}) == len(rows), "Event IDs collide")
    for name, r in found.items():
        check(r["callable"], name + " cannot be invoked")
        check(r["persistent"] == ([] if name == "CollectCore" else ["SharedLog"]), "Wrong persistent binding: " + name)
    return found


def exercise(scan_call, log_check):
    scan = scan_call("initial", None)
    log_check(EXPECTED[:1])
    found = buttons(scan, False)
    for step, name, opened, end in [("01-open","ButtonA",True,3), ("02-close","ButtonB",False,5),
                                    ("03-reopen","ButtonA",True,7), ("04-collect","CollectCore",False,8)]:
        scan = scan_call(step, found[name]["id"])
        log_check(EXPECTED[:end])
        found = buttons(scan, opened)
        print("Verified", step, flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", type=Path, default=ROOT / "Build/SwitchRoom.exe")
    args = parser.parse_args()
    exe = args.exe.resolve(strict=True)
    check((exe.parent / "GameAssembly.dll").is_file(), "Missing GameAssembly.dll")
    folder = Path(tempfile.mkdtemp(prefix="run-", dir=ROOT))
    log = folder / "Player.log"
    print("Evidence directory:", folder, flush=True)
    player = subprocess.Popen([str(exe), "-switchRoomVerify", "-logFile", str(log)], cwd=exe.parent)
    try:
        wait_for_log(log, player, EXPECTED[:1], 60)
        check("SWITCHROOM_TEST_INPUT_DISABLED" in log.read_text(encoding="utf-8", errors="replace").splitlines(),
              "Test input mode was not activated. Rebuild with Run-Test.cmd before retrying.")
        exercise(lambda step, event: invoke(player.pid, folder, step, event),
                 lambda expected: wait_for_log(log, player, expected, 5))
        print("PASS: Windows IL2CPP player and AutoVR-PC matched all four actions.")
    finally:
        if player.poll() is None:
            player.terminate()
        player.wait(timeout=15)


if __name__ == "__main__":
    main()
