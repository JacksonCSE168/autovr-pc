# Switch Room · AutoVR-PC 验收小游戏

游戏目标是打开保险库，点击红色面板中的 RECOVER CORE 收集能量核心。A 和 B 的按钮分别打开和关闭面板。两者共享一个在场景中序列化的 SharedLog 回调，各自再注册一个运行时回调。

## 在 Windows 运行

解压整个文件夹，双击 Run-Test.cmd。准备 Windows x64、已激活的 Unity 6 编辑器（含 Windows Build Support (IL2CPP)）、Visual Studio C++ 桌面开发工具和 Windows SDK，以及Python 3.11 x64（支持 py、python 和常见安装目录）。首次运行需要联网还原 Unity 包和 Python 依赖。自定义安装路径可将环境变量 UNITY_EDITOR 设为完整 Unity.exe 路径。

脚本自动生成场景、构建 Build/SwitchRoom.exe、启动游戏并调用包内原版 AutoVR-PC。验收脚本通过 -switchRoomVerify 参数关闭场景 EventSystem 的输入派发，游戏单独启动时可以正常用鼠标游玩。升级到此版本后首次使用 Run-Test.cmd 重新构建。脚本会在结束时关闭它启动的游戏。成功会显示 PASS，失败会留下 build.log 或 run-*/ 下的 Player.log、每步 JSONL 和命令输出。Build 文件夹整体保留后，可单独打开 EXE 玩，也可以用 .venv\Scripts\python.exe verify.py 再次测试。

## 验收动作

1. 初始扫描应找到 ButtonA 和 ButtonB。二者 ID 不同，均有一个 SharedLog 持久监听；CollectCore 隐藏。
2. 仅触发 A，应记录 shared、open，面板打开，出现 CollectCore。
3. 仅触发 B，应记录 shared、close，面板关闭，CollectCore 消失。
4. 再触发 A，然后触发 CollectCore。游戏计分应从 0 变为 1，关闭面板。

verify.py 同时核对 AutoVR-PC 的返回值、事件列表和独立 Player.log。出现额外回调、缺少回调、面板状态错误或计分错误均不能通过。测试使用已运行游戏的 PID。已在 Windows x64 上使用 Unity 6000.6.6f1 构建并通过四步实机验收。

## 用 Unity 打开

Unity Hub 中添加 Game 文件夹。首次打开后，点击 Switch Room 菜单中的 Create or rebuild demo scene，再点 Play。菜单会重新生成 Assets/SwitchRoom.unity。独立构建也会生成场景。
