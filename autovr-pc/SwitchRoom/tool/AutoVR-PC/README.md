# AutoVR-PC · Windows UnityEvent 测试

面向 Windows x64 的 Unity Standalone IL2CPP 游戏。目标目录中应有游戏 EXE、同目录的 GameAssembly.dll 和对应的游戏数据目录。可以直接连接已构建的游戏。Python 驱动和设备端脚本均在 Windows 上本地运行。

## 快速开始

1. 在 Windows 安装 64 位 Python 3.11，解压，在含 pc.py 的目录打开 PowerShell。
2. 运行以下两行。把第二行的路径换成游戏 EXE 的真实路径。

```powershell
py -3.11 -m pip install -r requirements.txt
py -3.11 pc.py --exe "C:\Games\AutoVRMiniLab\AutoVRMiniLab.exe"
```

第一轮只扫描。游戏已启动时，可以在任务管理器的「详细信息」中找到 PID，改用：

```powershell
py -3.11 pc.py --pid 1234
```

运行期间保持游戏正常更新。若 MiniLab 在窗口失焦时停止更新，可在自己的 Unity 工程中启用 Run In Background 后重新构建。若刚启动时场景尚未就绪，可让游戏停在主菜单后用 PID 再扫描。

## 单次事件和自动探索

每个事件包含 object、component、field、id、persistent、runtimeEntries 和 callable。persistent 列出 Inspector 配置的方法名；runtimeEntries 是运行时监听列表的长度，null 表示当前 Unity 布局未提供可读取的列表。callable 表示此刻可以尝试调用无参 Invoke。一个监听器为空的事件也可能正常返回。

如扫描显示某个按钮的 id 为 -1248/144，使用同一个运行中的游戏 PID：

```powershell
py -3.11 pc.py --pid 1234 --event=-1248/144
py -3.11 pc.py --pid 1234 --auto 10 --settle 1 --out run01.jsonl
py -3.11 pc.py --pid 1234 --scene 0
```

负数开头的 ID 使用等号形式。进程或场景重启、对象销毁或 UI 重建后需要重新扫描。--scene 接受 Build Settings 场景索引，会加载该场景。输出文件名需为新文件。触发动作会执行游戏自己的监听器并可能改变游戏状态。

自动模式按当前扫描顺序选择候选，每次调用后等待指定秒数，再从实际状态扫描。同一活动场景句柄下，同一个组件实例和字段最多尝试一次。firstSeenAfter 记录候选第一次被观察到之前的动作；定时器也可能改变状态。一次失败会留下 attempt 和 error 并停止。Invoke returned 表示事件调用正常返回；单个监听器的执行以及预期 UI 效果可以用游戏内日志分别验证。

## 和上传版 AutoVR 的对应关系

- event_graph.py 来源于 autovr/events.py。PC 驱动复用 EventNode 表示首次发现时的父子关系。
- ts/pc.ts 移植 ts/autovr/events.ts 的组件字段扫描和 m_Calls.m_RuntimeCalls 读取思路。扫描通过 UnityEngine.Object.FindObjectsOfType(Type) 枚举活跃组件，包括继承的实例字段。序列化监听方法名通过 UnityEventBase 查询。一个候选的身份由组件实例 ID 和字段偏移组成。
- pc.py 接管 autovr.py、app.py 和 run.py 中的启动、连接与调度职责。可选场景切换走 SceneManager，默认使用游戏的当前场景。
- 范围包括直接声明在组件上的 UnityEvent 字段（含 Button.onClick），调用范围为无参 Invoke。参数化事件可列出。嵌套对象中的事件、UI Toolkit、物理碰撞、多路径回放、键鼠输入、Mono 游戏和原 Android 网络测量不在本版范围。
- 本版交付独立的 PC 源码包，已附编译后的 ts/pc-agent.js。日常使用只需安装 Python 依赖。

## 检查与重新编译

```powershell
py -3.11 -m unittest discover -s tests
node tests/shared-listener.cjs
cd ts
npm ci
npm run build
```

Node 测试从编译包提取 PC 入口，以模拟 Unity 对象检查两个按钮共享回调以及其中一个按钮消失的情形。当前交付已通过脚本构建和模拟测试；Switch Room 已通过 Windows IL2CPP Player 四步实机验收。MiniLab 可让 A 和 B 都绑定 SharedLog，再分别绑定 OnlyA、OnlyB。单独选择 A 后查看 Player.log，预期出现 SharedLog 和 OnlyA；如果 A 打开面板，下一次扫描还应能看到面板下的按钮。
