# AutoVR-PC

A Windows x64 research prototype for discovering and invoking UnityEvents in Unity IL2CPP games. Adapted from [OSUSecLab/AutoVR](https://github.com/OSUSecLab/AutoVR). This repository contains the Windows tool, its precompiled Frida agent, and a small Unity game for testing shared callbacks.

## What the experiment checks

Switch Room has two active buttons that both call `SharedLog()`. A opens a vault and B closes it. Opening the vault reveals a third button, CollectCore. AutoVR-PC identifies an event by its component instance and field offset. The verifier chooses a prescribed action sequence and checks the resulting scans against the game's own callback and state log.

| Action | Expected observation |
| --- | --- |
| Open with A | Only A's action runs and CollectCore appears |
| Close with B | Only B's action runs and CollectCore disappears |
| Open again with A | CollectCore becomes available again |
| Collect the core | Score increases from 0 to 1 and the vault closes |

**Windows test result:** All four actions passed in the Switch Room Windows IL2CPP player built with Unity 6.6 (6000.6.6f1). The run verified this scene and this prescribed sequence. A comparison with the original Android implementation remains open.

## Run the Windows test

Use Windows x64, Unity 6 with Windows Build Support (IL2CPP), the Visual Studio C++ desktop build tools and Windows SDK, and Python 3.11 x64. From PowerShell at the repository root:

```powershell
.\SwitchRoom\Run-Test.cmd
```

The script builds the game, starts the player, and runs the four checks. A successful run prints `PASS: Windows IL2CPP player and AutoVR-PC matched all four actions.` To repeat the checks with the same build, run `.\SwitchRoom\Retest.cmd`.

## Source

- [AutoVR-PC](SwitchRoom/tool/AutoVR-PC/) — Python driver, TypeScript agent, and tests.
- [Switch Room](SwitchRoom/Game/) — Unity project and scene builder.
- [Verifier](SwitchRoom/verify.py) — action sequence and assertions.
- [Chinese setup guide](SwitchRoom/README.md) — setup and manual play instructions.

The upstream license is included in LICENSE. The bundled bridge has its own [license](SwitchRoom/tool/AutoVR-PC/BRIDGE-LICENSE.md).
