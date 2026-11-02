---
title: DSH 沙箱设计：一次 bash 调用，到底被关进了什么
date: 2026-11-02 14:20:00
categories:
  - Agent
tags:
  - Agent
  - DeepSeek
  - DSH
  - sandbox
cover: /images/DSH-沙箱设计/cover.jpg
---

前面三篇讲的是 DSH 的"软"的部分：[上下文怎么装配](/2026/10/30/DSH-上下文装配全解/)、[压缩怎么发生](/2026/10/30/DSH-会话压缩策略详解/)、[主循环怎么转](/2026/10/30/DSH-Agent主循环/)。这一篇讲"硬"的那一半——当模型说"我跑一下这条命令"的时候，是谁在替你把手指按在闸刀上。

我最初的问题很朴素，可能和你想的一样：

> 执行 bash 的时候，是不是启动一个沙箱，把文件挂载进去，再在里面跑 bash？

答案有点反直觉：**DSH 的本地沙箱里，没有"启动"这个动作，也没有"把文件挂载进去"这件事。**它做的是在 `bash -c "..."` 这个命令的**前面插一段参数**，让内核在真正 exec 之前，先把进程丢进一个被裁剪过的视野里。

这篇文章就把这件事从头拆到尾：为什么要有它、它到底在哪一步生效、关进去之后能看见什么、被拦下来之后又会发生什么。

## 0. 一句话概括

> 本地沙箱不是虚拟机、不是容器，是**同一个世界里给一条命令戴的手套**：整块磁盘只读、工作区和 `/tmp` 可写、进程看不见别的进程。
>
> 它不是一个"模块"，而是三条独立的缝：**契约**（`ctx.sandbox`）、**策略**（`ctx.sandboxPolicy`）、**后端**（`sandbox-local`）。
>
> 每次执行都重新解析一次策略；`danger-full-access` 直接短路，连手套都不戴。

## 1. 先纠正一个直觉

大多数人对"沙箱"的印象来自 Docker：起一个容器，把工作目录 `-v` 挂进去，`docker exec` 跑命令。这个印象很自然，因为"隔离"通常意味着"换一个环境"。

DSH 走的是另一条路。看 `dsh-bash-sandbox` 里真正的那几行——它把本地 bash 的执行器整个继承下来，只在最后一步做了替换：

```js
// dsh-bash-sandbox/lib/index.js:161-167
confine(command, policy, signal) {
  return this.ctx.sandbox.confine([
    "bash",
    "-c",
    command
  ], policy, signal);
}
```

`confine` 的产物不是"一个沙箱实例"，而是**一段新的 argv**。在 macOS 上，它大概长这样：

```
sandbox-exec -p '(version 1) (allow default) (deny file-write*) ...' -- bash -c "你的命令"
```

在 Linux 上长这样：

```
bwrap --ro-bind / / --dev /dev --unshare-pid --proc /proc --die-with-parent \
      --tmpfs /tmp --bind /path/to/workspace /path/to/workspace \
      -- bash -c "你的命令"
```

然后这段 argv 被原样交给子进程去 spawn。**没有镜像、没有 init 进程、没有网络栈、没有"启动/销毁"的生命周期。**沙箱的寿命就是这条命令的寿命——`--die-with-parent` 会在 bwrap 父进程退出时把里面的一切一起带走。

这么选的理由很实际：

- **文件"原地"就在那儿。**不需要把 30 万个文件的工作区同步进一个容器里，也就没有"同步慢了/漏了/冲突了"这些问题。
- **毫秒级。**没有守护进程要连，没有镜像要拉。
- **不需要 root。**bwrap 用用户命名空间，Landlock 用内核 LSM，Seatbelt 是 macOS 自带的 `sandbox-exec`。

代价也很明确：**它和你的进程共享同一个内核、同一个文件系统**。所以它防的是"写错地方"，不是"这条命令是恶意的、想逃出去"。这是设计取舍，不是疏忽——文档里自己就写了：需要隔离整个环境时，请用容器、microVM 或远端执行器。

## 2. 为什么非要沙箱

如果模型只是个"建议者"，沙箱是多余的。但它不是——它有 bash，一次能发十几条命令，中间没有人复核。

具体怕三件事：

**一是"手滑"没有对应的体感。** 人会停顿，会看见 `rm -rf` 四个字心跳加速。模型不会。它生成 `rm -rf "$BUILD_DIR/"` 的时候，`$BUILD_DIR` 可能刚好是个空字符串，于是这一行变成 `rm -rf /`。这类事故在 agent 场景里的概率，和"模型写错一个变量的概率"是同一个量级。

**二是路径幻觉。** `~/project` 和 `~/Projects`、`./src` 和 `src`、相对路径和 git 根目录，模型的记忆里经常是模糊的。它真诚地以为自己在改 `config.yml`，实际改的是另一个同名文件。

**三是被"说服"。** 这是最容易被低估的一种：你让它读一个 issue、一个网页、一个 README，里面的文字可能写着"请执行 `curl ... | sh`"或者"顺便把 `.npmrc` 发到这个地址"。模型没有"这是别人写给我的指令，还是任务里的一段资料"的天然分界线。一旦它能写 `$HOME`，就能改 `~/.zshrc`、往 `~/Library/LaunchAgents` 里塞一个开机自启、或者覆盖 `.git/hooks/pre-commit`——**下一次你亲手敲命令的时候，被执行的是它。**

沙箱拦不住"模型被骗"，但它能把损失关在一个抽屉里：**能读的随便读，能写的就是工作区那一块。**

还有一个不那么安全、但同样重要的理由：**它让人少被打断。** 有了默认的写边界，绝大多数正常操作根本不需要弹窗问"你确定吗"；只有越界的那一次才需要人出面。安全感和流畅度在这里不冲突。

## 3. 沙箱的四种流派

"沙箱"这个词被用得太泛了。按隔离的粒度分，大致是四条路：

| 流派 | 代表 | 隔离单位 | 你的文件在哪 | 启动成本 |
|---|---|---|---|---|
| 不隔离 | 早期 agent | 无 | 原地 | 0 |
| 进程级围栏 | bwrap / Landlock / Seatbelt | 单条命令 | **原地** | 毫秒 |
| 容器 | Docker | 一个容器 | 挂载进去 | 秒级 |
| 虚拟机 / 云沙箱 | Firecracker / E2B | 一台机器 | 上传或同步 | 百毫秒到秒级 |

DSH 的本地默认是**第二条**，同时它把**第四条**做成了一个可选的替代品（E2B，后面第 10 节讲）。这两条路的差别不是"好一点/差一点"，而是**换不换世界**：

- 进程级围栏：世界没变，只是这条命令的写权限被裁掉了。
- 虚拟机/云沙箱：换了一个世界，文件系统、进程表、网络全是新的。

所以"要不要上沙箱"其实是个更前面的问题：**你是想管住"写哪里"，还是想管住"整个环境"？** 前者一条命令一层壳就够了，后者才需要搬家。

## 4. 三条缝：沙箱不是一个包

DSH 把这件事拆得很干净，干净到第一次看会觉得"至于吗"。三个包各管一件事：

{% mermaid %}
flowchart LR
  subgraph TOOL["工具层（模型看得到的）"]
    T1["tool-bash"]
    T2["tool-fs"]
    T3["tool-pwsh"]
  end
  subgraph CAP["能力层（可整体替换）"]
    S1["ctx.shell<br/>执行器"]
    S2["ctx.fs<br/>文件系统"]
  end
  subgraph SB["沙箱层"]
    C["ctx.sandbox<br/>confine(argv, policy)"]
    P["ctx.sandboxPolicy<br/>mode + workspaceRoot"]
  end
  subgraph BE["后端（按平台选）"]
    B1["bwrap"]
    B2["landlock"]
    B3["sandbox-exec"]
    B4["windows-acl"]
  end
  T1 --> S1
  T3 --> S1
  T2 --> S2
  S1 --> C
  S2 --> P
  C --> B1
  C --> B2
  C --> B3
  C --> B4
  P -.->|"每次调用交出 policy"| C
  P -.->|"每次写操作交出 policy"| S2
{% endmermaid %}

- **`dsh-sandbox` 只是词汇表。** 它定义 `SandboxMode`、`ConfinedArgv`、拒绝标记、升级阶梯，以及一个 `SandboxProvider` 服务；**它不依赖任何具体后端**。所以"沙箱"这个概念本身可以被别的实现接管。
- **`dsh-sandbox-policy` 是策略的唯一归属者。** 当前模式、工作区根、以及"谁能改模式"都在这儿。
- **`dsh-sandbox-local` 是后端实现。** 它挑平台、探针、拼 profile，把 argv 包好交回去。
- **消费者只做一件小事。** `dsh-bash-sandbox` 把 `ctx.shell` 换成"会包装的 bash"，`dsh-fs-sandbox` 把 `ctx.fs` 换成"带栅栏的文件系统"，`dsh-pwsh-sandbox` 是 PowerShell 版的同一件事。

拆成三条缝的好处，用一句话说就是：**工具层完全不知道沙箱存在。** 模型看到的 `bash` 工具描述、参数、返回格式，一个字都没变；换后端、改策略、甚至把整个本地后端换成远端，都不需要动工具。反过来，模型也**不会**因为"有个沙箱"就以为每条命令都必然被关着——它看到的是"可能被关着"，以及被关时的具体提示。

## 5. 什么时候会被关进去

这里最容易误解：没有"进入沙箱模式"这种开关，**每一次调用都独立解析一次策略**。

{% mermaid %}
flowchart TD
  A["模型发起 bash 调用"] --> B["tool-bash 解析参数<br/>command / workdir / sandbox_permissions"]
  B --> C{"resolve() 得到 mode"}
  C -->|"danger-full-access"| D["短路：不包装<br/>直接 spawn"]
  C -->|"read-only / workspace-write"| E["ctx.sandbox.confine(argv, policy)"]
  E --> F{"该平台有可用 runner？"}
  F -->|"没有"| G["抛 SANDBOX_UNAVAILABLE<br/>拒绝裸跑"]
  F -->|"有"| H["返回包装后的 argv"]
  H --> I["spawn 子进程"]
  I --> J{"退出码 + stderr"}
  J -->|"命中拒绝方言"| K["sandbox.denied = true<br/>返回拒绝标记"]
  J -->|"命中 runner 致命签名"| L["抛 SANDBOX_UNAVAILABLE<br/>命令根本没跑"]
  J -->|"正常"| M["返回 stdout / stderr"]
{% endmermaid %}

`mode` 从哪来？三级，从强到弱：

1. **本次调用显式批准的更宽模式**（模型申请、人点了"允许一次"）；
2. **本会话最后一次 `sandbox/mode` 事件**（你在界面上切了权限档）；
3. **部署默认值**：`$DSH_PERMISSION_MODE`，base 组合里没设就是 `workspace-write`。

源码里就一行：

```js
// dsh-sandbox-policy/lib/index.js:141-148
resolve(request = {}) {
  const { session } = request;
  return {
    mode: request.mode ?? (session === void 0 ? void 0 : this.overrideOf(session)) ?? this.defaultMode,
    workspaceRoot: resolveWorkspaceRoot(session?.header.cwd ?? this.workspaceRoot),
    ...session === void 0 ? {} : { sessionId: session.id }
  };
}
```

注意 `workspaceRoot` 的取值：**跟着会话的 cwd 走**，没有会话才退回到配置里的根。这就是"可写范围"的边界——不是"当前目录"，而是"这个会话认领的工作区"。

还有个细节很有意思：**模型自己也能看到当前策略。** 每次请求装配时，`sandbox:policy` 这一段会被拼进系统提示词的上下文区（不是稳定的系统提示词本体，所以不影响缓存前缀）。三句话，按档位不同：

```text
Current DSH file policy: read-only. Any available operation enforced by the DSH file
sandbox cannot modify files in the standing mode. Do not refuse a required modification
from this policy alone: try an available tool normally and follow any denial and
escalation guidance it returns.
```

`workspace-write` 那句会把工作区路径直接写进去；`danger-full-access` 那句则明说"不限制"。为什么要告诉模型？因为**它得知道自己会被拦，而且被拦了不该自己放弃**——第二句"Do not refuse a required modification from this policy alone"就是防止模型看到只读就回你一句"我改不了，你自己动手吧"。

## 6. 关进去之后，能看见什么

这是全文最"实"的部分。以 Linux 的 bwrap 为例，profile 就是下面这 15 行：

```js
// dsh-sandbox-local/lib/index.js:22-39
function bwrapProfileArgs(policy) {
  const args = [
    "--ro-bind", "/", "/",
    "--dev", "/dev",
    "--unshare-pid",
    "--proc", "/proc",
    "--die-with-parent"
  ];
  if (policy.mode === "workspace-write") {
    args.push("--tmpfs", "/tmp");
    args.push("--bind", policy.workspaceRoot, policy.workspaceRoot);
  }
  return args;
}
```

逐条翻译：

| 参数 | 含义 | 效果 |
|---|---|---|
| `--ro-bind / /` | 把宿主根目录**只读**绑定到同一位置 | 全世界都能看，谁都改不了 |
| `--dev /dev` | 挂一个最小的 `/dev` | 有 `/dev/null` 这类设备，没有宿主的其他设备 |
| `--unshare-pid` | 私有 PID 命名空间 | 看不见宿主的进程 |
| `--proc /proc` | 在私有命名空间里挂 `/proc` | 只能看到自己这一支的进程 |
| `--die-with-parent` | 父进程死，子进程跟着死 | 没有"孤儿进程在后台偷偷干活" |
| `--tmpfs /tmp` | 全新的空 `/tmp` | 临时文件可以写，但**只在这个进程活着的时候存在** |
| `--bind <ws> <ws>` | 工作区读写绑定 | 唯一"持久可写"的地方 |

`--unshare-pid` 和 `--proc` 这一对值得多说一句。它们不只是为了"看不见别的进程"——**procfs 是个后门**：`/proc/self/cwd`、`/proc/self/root` 这类魔术链接指向的是文件系统里真实的位置，如果你把宿主的 `/proc` 挂进去，一条 `cd /proc/1/root && ...` 就能绕开你精心布置的挂载。所以私有 PID 命名空间 + 自己挂的 `/proc` 是**成对出现**的，缺一个就漏了。

macOS 没有命名空间，用的是另一套：Seatbelt 的策略语言（SBPL）。

```js
// dsh-sandbox-local/lib/index.js:65-75
function seatbeltProfileArgs(policy) {
  const forms = [
    "(version 1)",
    "(allow default)",
    "(deny file-write*)",
    `(allow file-write* (literal ${sbplString("/dev/null")}))`
  ];
  const roots = writableRoots(policy);
  if (roots.length > 0) forms.push(`(allow file-write* ${roots.map((root) => `(subpath ${sbplString(root)})`).join(" ")})`);
  return ["-p", forms.join(" ")];
}
```

"默认全允许，然后把**所有写**禁掉，再按白名单一个个开回来"——读和写在这里被彻底分开了，这就是为什么只读模式几乎是零成本的。

`writableRoots` 是个共享函数（`dsh-sandbox/lib/index.js:166-173`）：只读模式返回空数组；`workspace-write` 返回 `[工作区, "/tmp", 系统临时目录]`，而且会**先 canonicalize 再去重**——因为 macOS 上 `/tmp` 其实是 `/private/tmp` 的软链，不解析就会白名单和实际路径对不上。

### 本机实测

光看代码不算数。我这台机器是 macOS，正好是 Seatbelt 后端，直接打三条命令：

```bash
$ touch /tmp/dsh-demo && echo "tmp: OK"
tmp: OK
$ touch ~/dsh-demo
touch: /Users/smzdm/dsh-demo: Operation not permitted
$ echo hi > /usr/local/bin/dsh-demo
bash: /usr/local/bin/dsh-demo: Operation not permitted
$ touch /Users/smzdm/chw/dsh-demo      # 工作区的上一级
touch: /Users/smzdm/chw/dsh-demo: Operation not permitted
$ head -1 ~/.zshrc                     # 读？随便读
# ===== oh-my-zsh =====
```

四行输出把模型解释得很清楚：

- 整块盘**可读**（`~/.zshrc` 随便看）；
- `/tmp` **可写**；
- 工作区（`/Users/smzdm/chw/BlogCode`）**可写**；
- 工作区的**父目录** `/Users/smzdm/chw` 不可写——边界正好落在会话认领的那个目录上。

<p align="center">
  <img src="/images/DSH-沙箱设计/write-scope.png" width="780" alt="一个世界，两份写权限" style="border-radius:12px;">
</p>

这也顺带解释了很多人第一次用 DSH 时会碰到的那句话：

```text
[sandbox: file access denied under workspace-write mode]
```

它不是"出错了"，是**策略生效了**。

## 7. 被拒绝了会怎样

一条命令被拦下来，故事没结束，反而才刚开始。DSH 在这里设计了一条很克制的链路：**标记 → 提示 → 申请 → 审批 → 一次放宽**。

{% mermaid %}
sequenceDiagram
  participant M as 模型
  participant T as tool-bash
  participant S as ctx.sandbox
  participant H as 人
  M->>T: bash("touch ~/x")
  T->>S: confine(argv, workspace-write)
  S-->>T: 包装后的 argv
  T->>T: spawn，stderr 报 Operation not permitted
  T-->>M: sandbox.denied=true + 拒绝标记
  Note over M: 看到了升级提示
  M->>T: bash("touch ~/x", sandbox_permissions=danger-full-access, justification=...)
  T->>H: 审批请求
  H-->>T: 允许一次
  T->>S: confine(argv, danger-full-access)
  Note over S: 短路，不包装
  T-->>M: 成功
{% endmermaid %}

第一步是**结构化的事实**，不是一句自然语言。结果对象里带着 `sandbox: { mode, denied, enforcement }`，工具层据此在输出里贴标记：

```text
[sandbox: file access denied under workspace-write mode]
```

同一个标记后面还会跟一句提示（`dsh-sandbox/lib/index.js:76-78`），措辞是固定的：

```text
[sandbox: escalation available — retry this exact command once with sandbox_permissions
(the narrowest wider mode that suffices) + justification; the approval prompt asks the user]
```

"**the narrowest wider mode**"和"**this exact command**"是两个刻意的约束：只准往宽了走、不准顺带改命令。因为如果模型能借一次升级把命令也换了，那审批就形同虚设——你批的是"写 `/tmp`"，执行的可能是别的东西。

升级阶梯是个闭表（`dsh-sandbox/lib/index.js:30-33`）：

| 当前模式 | 可申请到 |
|---|---|
| `read-only` | `workspace-write` / `danger-full-access` |
| `workspace-write` | `danger-full-access` |
| `danger-full-access` | 无（已经最宽） |

审批本身走 `ctx.approval`，返回四种结果之一：`allowed-once` / `rejected` / `cancelled` / `unavailable`。三种不是"允许"的情况都**不等于**自动放宽——`unavailable` 意思是"这个组合里根本没有审批通道"，那就老老实实失败。还有两个小规矩：同一个模式的"申请"直接放行不再打扰人；往窄了申请直接报错。

值得单独说的是**"runner 失败"和"命令被拒"必须分开**。沙箱进程自己起不来（比如 bwrap 没装、Seatbelt 拒绝加载策略），和命令因为越界被内核拒绝，在 stderr 里可能只差一行字。前者如果被误判成后者，模型会以为"我只是权限不够"，然后去申请升级——而真正该做的是修环境。所以每个后端都带一份"致命签名"表（`dsh-sandbox-local/lib/index.js:231-243`）：

| 后端 | 致命标志 | 退出码约束 |
|---|---|---|
| bwrap | `bwrap: ` 开头 | 只认签名 |
| landlock | `landlock-run: ` 开头 | 必须 125 |
| seatbelt | `sandbox-exec: ` 开头 | 只认签名 |
| windows-acl | `windows-acl-run: ` 开头 | 必须 127 |

命中就抛 `SANDBOX_UNAVAILABLE`，并明确告诉模型"命令**没有执行**，这是沙箱的问题，不是命令失败"。

## 8. 写文件那条路：栅栏，不是边界

bash 是被内核关起来的，那 `write` / `edit` 这两个工具呢？它们不走 bash，走的是 harness 自己的文件系统服务。

这里有一个非常清醒的注释（`dsh-fs-sandbox/lib/index.js:77-85`）：

```text
The fence is a policy check in TRUSTED code over a MODEL-CONTROLLED path,
NOT a kernel boundary — the operations are the seam's own (open, rename),
and only the target path is untrusted, so canonicalize-then-contain is the
complete answer to this surface. This is containment, not a security
boundary; kernel-grade isolation of untrusted CODE stays ctx.shell's job.
```

翻译成人话：**这条路上"跑什么代码"是可信的（是我们自己的 `open`），不可信的只有"路径"这个字符串。** 所以不需要内核边界，把路径校验到位就够了。

具体做法是 **canonicalize-then-contain**，而且刻意多走半步：

```js
// dsh-fs-sandbox/lib/index.js:153-166
async checkedTarget(target, sandboxPolicy) {
  const policy = sandboxPolicy ?? this.ctx.sandboxPolicy.resolve();
  const { mode } = policy;
  if (mode === "danger-full-access") return target;
  if (mode === "read-only") throw new FsError(`cannot write "${target.displayPath}": file access denied under read-only mode`, "FS_SANDBOX_DENIED");
  const fresh = await this.resolve(target.displayPath);
  let contained = false;
  for (const root of writableRoots(policy)) if (await isPathUnder(fresh.targetKey, root)) {
    contained = true;
    break;
  }
  if (!contained) throw new FsError(`cannot write "${target.displayPath}": file access denied under workspace-write mode`, "FS_SANDBOX_DENIED");
  return fresh;
}
```

两个细节：

- **返回的是 `fresh`，不是原来的 `target`。**检查用的那个路径，和真正被写的那个路径，是同一个对象——这样就不存在"检查 A、写 B"的问题。
- **在委托之前重新 canonicalize 一次。**因为从检查到真正落盘之间，攻击者可能把某一级祖先目录换成软链（TOCTOU）。重新解析能把窗口缩到最小，剩下的残余风险被明确写进注释、并**接受**了——因为威胁模型是"模型写错路径"，不是"本地有恶意进程和我赛跑"。

`isPathUnder` 本身也值得一提：先走廉价的字符串比较，词法上不在根下面时，再沿着目标路径往上找**已存在的祖先**，用 `(dev, ino)` 比对文件身份。这是为了兜住 Windows 的 8.3 短名和大小写不敏感这类"拼写不同、其实是同一个文件"的情况——纯字符串比较在这里会漏。

所以两条路的分工是清楚的：

| | bash | fs（write/edit） |
|---|---|---|
| 跑的是谁的代码 | 模型写的任意代码 | harness 自己的 open/rename |
| 边界性质 | 内核边界 | 可信代码里的策略检查 |
| 不可信的东西 | 整个进程 | 只有目标路径 |
| 拒绝形态 | 内核 errno（EPERM/EROFS） | 结构化 `FS_SANDBOX_DENIED` |
| 读 | 放行 | 放行 |

## 9. 四个后端，四种方言

同一份策略，落到不同平台上说法不一样。这是 `PLATFORM_CHAINS` 和几张表拼起来的事实（`dsh-sandbox-local/lib/index.js:173-243`）：

| 平台 | 选择链 | 机制 | enforcement | 拒绝方言 |
|---|---|---|---|---|
| Linux | `bwrap` → `landlock` | 用户命名空间 + 挂载 | full | `read-only file system` |
| Linux | `landlock` | 内核 LSM，不需要 root | full（老 ABI 可能 partial） | `permission denied` |
| macOS | `seatbelt` | `sandbox-exec` + SBPL | full | `operation not permitted` |
| Windows | `windows-acl` | 受限令牌 + ACL | **partial** | `access is denied` 等 |

三条规则值记住：

**一、先按平台选，再做探针。** Linux 有两个候选，所以会在第一次需要时**功能性地试一遍**（真的跑一次 `bwrap ... -- true`，退出码 0 才算可用），结果缓存在 provider 生命周期里。macOS 只有 `sandbox-exec` 一个候选，**根本不探**——没有备选的时候，探针没有意义，只会增加启动延迟。这条"探针只用来仲裁，不用来复核唯一选择"的取舍，代码注释里写得很直白。

**二、enforcement 是"报告的事实"，不是"承诺"。** 每个包装返回值都带 `enforcement: 'full' | 'partial'`。Windows 的 ACL 方案是 partial——它管不住硬链接、管不住未受限进程的读、也管不住 AppContainer 的 ACL 边界。老版本 Landlock ABI 同理。需要绝对边界的调用方可以直接拒绝 partial。

**三、失败要失败得"响"。** 平台没有链、或者链上每个探针都失败，`confine()` 不是"算了裸跑吧"，而是抛错：

```text
sandbox mode "<mode>" is requested but no sandbox backend is usable on this host;
refusing to run the command unconfined. Install bubblewrap or run a Landlock-enforcing
kernel (Linux), ensure sandbox-exec is usable (macOS), or ensure the ACL restricted-token
runner can start (Windows) — otherwise switch the consumer to danger-full-access.
```

**"refusing to run the command unconfined"** ——这句话是整个设计的地基。宁可失败，也不悄悄降级。因为悄悄降级是安全的反面：用户以为有保护，实际没有，而且永远不会知道。

## 10. 另一条路：E2B 把整个世界换掉

前面说的都是"同世界围栏"。如果确实需要另一个世界——比如要跑一段来源不明的代码、要限制网络、要让文件系统从零开始——那就不是换个后端能解决的，得**换掉能力本身**。

E2B 就是这样一套东西，DSH 把它做成了三个包：

| 包 | 替换了什么 | 职责 |
|---|---|---|
| `e2b` | 新增 `ctx.e2b` | 沙箱的生命周期所有者：构造即创建，销毁即删除 |
| `fs-e2b` | **替换** `ctx.fs` | 所有文件操作打到远端 Linux 沙箱 |
| `subprocess-e2b` | **替换** `ctx.subprocess` | 所有子进程在远端跑，字节流回传 |

注意它**不是** `ctx.sandbox` 的后端——它压根不走 `confine` 这条缝。这是两个层次的替换：本地沙箱是"给命令戴手套"，E2B 是"把工作台整个搬走"。

几个实际参数：

- `cwd` 默认 `/home/user/workspace`，必须是绝对 POSIX 路径，**它是解析约定，不是 containment**（里面的程序照样能寻址别的路径）；
- `timeoutMs` 默认 300000，到点删沙箱；
- `apiKey` 只配给宿主侧的 SDK，**从不装进沙箱**；
- 不搬过去的东西：harness 进程本身、agent 状态、会话日志、LLM 请求、技能——这些全留在本地。

而且它是**实验性的、opt-in 的**：任何出厂组合（base / headless / web-app）都**不默认挂载**。要用得自己在 profile 里声明三个插件，而且 `fs-e2b`、`subprocess-e2b` 必须排在 `e2b` 之后加载。

所以选型其实很简单：

{% mermaid %}
flowchart LR
  Q{"要隔离的是什么？"} -->|"写错地方"| A["本地沙箱<br/>confine(argv)"]
  Q -->|"整个环境<br/>网络/依赖/不可信代码"| B["E2B<br/>替换 ctx.fs + ctx.subprocess"]
  A --> A1["同内核，同文件系统<br/>毫秒级，无需 root"]
  B --> B1["独立 Linux 沙箱<br/>远程，状态短暂"]
{% endmermaid %}

## 11. 它明确不做什么

一份诚实的设计说明，得把边界写清楚。DSH 的本地沙箱**只管文件写**：

- **不管网络。**命令照样能 `curl` 出去。
- **不管进程数量、CPU、内存。**没有 cgroup 配额。
- **不管 syscall 和内核攻击面。**共享内核，只是换了挂载视图。
- **不管设备。**`/dev` 只是最小集合，不是白名单。
- **不管凭据。**它不会替你清掉环境变量里的 token。
- **读永远放行。**所以 `~/.ssh`、`~/.aws`、钥匙串，只要进程知道路径，就能读。

再加几条工程上的限制：一个 context 只能有一个 provider；拒绝的分类靠 stderr 方言推断（内核不给结构化通道）；Windows 只有 partial。

知道这些之后，"沙箱"这个词就不该被理解成"安全了"，而应该理解成**"默认把破坏半径压到最小"**。真正的隔离，要么上容器/虚拟机，要么在它外面再加一层网络和凭据的边界。

## 12. 自己动手验证

三步，都能在你自己的机器上复现。

**第一步，看这个组合到底挂了哪些沙箱包：**

```bash
dsh web --dump-config | grep -iE "sandbox"
```

正常情况下你会看到 `sandbox`、`sandbox-policy`、`sandbox-local`，以及某个 `*-sandbox` 执行器（bash 或 pwsh）。看不到 `e2b` 是对的——它默认不挂。

**第二步，看默认策略：**

```bash
echo $DSH_PERMISSION_MODE       # 没设就是组合里的默认值
```

**第三步，直接撞一次边界：**

```bash
touch /tmp/ok && echo "tmp 可以写"
touch ~/nope && echo "不该看到这一行"
echo hi > /usr/local/bin/nope
head -1 ~/.zshrc                # 读是不设防的
```

如果你看到 `Operation not permitted`，说明 Seatbelt 在工作；看到 `Read-only file system`，那是 bwrap；`Permission denied` 则是 Landlock。三种方言，一个意思。

最后，如果你想知道"为什么模型总说自己的权限不够"，翻回第 5 节——它每次请求都会收到一句 `Current DSH file policy: ...`，那是它对自己处境的唯一知情来源。

## 小结

把这篇的骨架压缩成五句话：

1. 沙箱防的是"写错地方"，不是"恶意逃逸"——所以它选了最轻的那条路：给命令戴手套，而不是搬家。
2. 没有"启动沙箱"这一步，只有"把 argv 包一层"；沙箱的寿命等于命令的寿命。
3. 三条缝各管一件事：契约（能不能包）、策略（包成什么样）、后端（用谁包）。
4. 每次调用重新解析策略，三级优先，`danger-full-access` 短路；失败宁可报错也不裸跑。
5. 被拦下不是一个终点，而是一条固定链路：标记 → 提示 → 只准变宽的申请 → 人工审批。

下一篇想聊工具系统（一个 bash 工具描述为什么能写那么长），或者子代理与团队。看完有想深挖的点，直接说。

**相关阅读**：

- [DSH 上下文装配全解](/2026/10/30/DSH-上下文装配全解/)：一次模型请求到底是怎么拼出来的
- [DSH 会话压缩策略详解](/2026/10/30/DSH-会话压缩策略详解/)：上下文快满了怎么办
- [DSH Agent 主循环](/2026/10/30/DSH-Agent主循环/)：一条用户消息的完整旅程
- [Agent Sandbox：为什么 AI Agent 需要一个安全的执行环境](/2026/04/28/Agent-Sandbox-安全执行环境/)：偏概念的入门版，可以对照着看
