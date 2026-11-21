"""AutoVR UnityEvent explorer for Windows standalone IL2CPP players."""
import argparse
import asyncio
import json
from pathlib import Path
import subprocess
import sys
import time

from event_graph import EventNode


async def rpc(api, name, *args):
    result = await asyncio.wait_for(getattr(api, name)(*args), timeout=30)
    if not result["ok"]:
        raise RuntimeError(result["error"])
    return result["value"]


async def explore(api, limit, settle, record):
    """Keep AutoVR's event-node ancestry while rescanning the actual live state."""
    attempted = set()
    parent_by_event = {}
    root = EventNode("initial")
    parent = root
    for step in range(limit + 1):
        scan = await rpc(api, "scan")
        record({"type": "scan", **scan})
        candidates = []
        for event in scan["events"]:
            key = (scan["sceneHandle"], event["id"])
            if key not in parent_by_event:
                node = EventNode(event["id"], parent)
                parent.addChild(node)
                parent_by_event[key] = node
            if event["callable"] and key not in attempted:
                candidates.append((key, event))
        if step == limit or not candidates:
            return
        key, event = candidates[0]
        attempted.add(key)
        node = parent_by_event[key]
        record({"type": "attempt", "scene": scan["scene"], "event": event,
                "firstSeenAfter": node.parent.event_name})
        result = await rpc(api, "trigger", event["id"])
        node.markTriggered()
        parent = node
        record({"type": "result", **result})
        await asyncio.sleep(settle)


async def run(args, record):
    import frida
    device = frida.get_local_device()
    if args.exe:
        exe = args.exe.resolve(strict=True)
        if not (exe.parent / "GameAssembly.dll").is_file():
            raise RuntimeError("Expected GameAssembly.dll beside the Windows IL2CPP player.")
        player = subprocess.Popen([str(exe)], cwd=exe.parent)
        pid = player.pid
    else:
        pid = args.pid
    session = device.attach(pid)
    try:
        agent = Path(__file__).parent / "ts" / "pc-agent.js"
        script = session.create_script(agent.read_text(encoding="utf-8"))
        script.on("message", lambda msg, data: print(msg, file=sys.stderr))
        script.load()
        api = script.exports_async
        deadline = time.monotonic() + 30
        while not await asyncio.wait_for(api.ready(), 5):
            if time.monotonic() >= deadline:
                raise RuntimeError("GameAssembly.dll was not detected. Check the PID and scripting backend.")
            await asyncio.sleep(.25)
        if args.scene is not None:
            await rpc(api, "load_scene", args.scene)
            deadline = time.monotonic() + 30
            while await rpc(api, "active_index") != args.scene:
                if time.monotonic() >= deadline:
                    raise RuntimeError("Timed out waiting for the requested scene.")
                await asyncio.sleep(.2)
            await asyncio.sleep(args.settle)
        if args.event:
            record({"type": "attempt", "id": args.event})
            record({"type": "result", **await rpc(api, "trigger", args.event)})
            await asyncio.sleep(args.settle)
        await explore(api, args.auto or 0, args.settle, record)
    finally:
        session.detach()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--pid", type=int, help="PID of a running Windows Unity player")
    target.add_argument("--exe", type=Path, help="launch a Windows IL2CPP player")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--event", help="invoke the exact event ID from a scan of this running player")
    mode.add_argument("--auto", type=int, metavar="LIMIT", help="explore up to LIMIT currently reachable events")
    parser.add_argument("--scene", type=int, help="optional scene build index")
    parser.add_argument("--settle", type=float, default=.5, help="seconds to wait after an invocation")
    parser.add_argument("--out", type=Path, help="write JSON lines to a new file")
    args = parser.parse_args()
    if args.settle < 0 or (args.auto is not None and args.auto < 1):
        parser.error("--auto must be positive and --settle must be nonnegative")
    if sys.platform != "win32":
        parser.error("Run in native Windows Python.")
    stream = args.out.open("x", encoding="utf-8") if args.out else None
    def record(value):
        line = json.dumps(value, ensure_ascii=True)
        print(line, flush=True)
        if stream:
            print(line, file=stream, flush=True)
    try:
        asyncio.run(run(args, record))
    except (Exception, KeyboardInterrupt) as error:
        record({"type": "error", "message": str(error) or type(error).__name__})
        return 1
    finally:
        if stream:
            stream.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
