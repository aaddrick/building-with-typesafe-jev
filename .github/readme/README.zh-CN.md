<p align="center">
  <strong>Building with TypeSafe Jev</strong><br>
  <em>为你的编程智能体提供带校准置信度的类型化决策。</em><br>
  <em>链接到 150 多个社区项目，按形态分类，每种形态附一个代码草图。</em>
</p>

<p align="center">
  <a href="../../LICENSE"><img src="https://img.shields.io/github/license/aaddrick/building-with-typesafe-jev?style=flat" alt="License"></a>
  <a href="../workflows/checks.yml"><img src="https://img.shields.io/github/actions/workflow/status/aaddrick/building-with-typesafe-jev/checks.yml?label=checks&style=flat" alt="Checks"></a>
</p>

<p align="center">
  <a href="https://www.linkedin.com/in/aaddrick/">在 LinkedIn 上联系我！</a>
</p>

<p align="center">
  <a href="../../README.md">English</a> ·
  <strong>简体中文</strong> ·
  <a href="README.ja.md">日本語</a> ·
  <a href="README.ko.md">한국어</a> ·
  <a href="README.vi.md">Tiếng Việt</a> ·
  <a href="README.pt-BR.md">Português (BR)</a> ·
  <a href="README.it.md">Italiano</a>
</p>

> [!NOTE]
> 这是一个非官方的社区技能。它不是由 TypeSafe AI 制作、审核或认可的。TypeSafe 在 [typesafe-ai/skills](https://github.com/typesafe-ai/skills) 发布了自己的技能。参见[与官方技能的区别](#与官方技能的区别)。

编程智能体把 Jev 当作又一个聊天模型。这个技能教它们为 Jev 做设计：类型化的问题、校准过的置信度，以及指向 150 多个社区项目的链接，按工作方式分类，每种模式附一个代码草图。它可以安装在 Claude Code、Codex、Antigravity CLI、Muse 和 Muse Code 中。

[Jev](https://docs.typesafe.ai/introduction) 是一个 [System One](https://docs.typesafe.ai/concepts/system-one) 模型。它不生成文本。你给它发送内容和一组类型化的问题，它对每个问题返回一个值和一个校准过的概率，通常在 100 到 200 毫秒内完成：

- **Choice** 从列表中选出一个选项。例如：把工单分派给账单、物流或客服。
- **Score** 把内容放到一个由你描述的等级上。例如：在"忽略规格"到"符合规格"之间给一个 pull request 打分。
- **Noul** 给出一个是/否陈述为真的概率。例如："这条 shell 命令会删除项目之外的文件。"

## 安装

<details>
<summary><strong>Claude Code</strong></summary>

```bash
claude plugin marketplace add aaddrick/building-with-typesafe-jev
```

```bash
claude plugin install building-with-typesafe-jev@building-with-typesafe-jev
```

你在写 Jev 代码时，技能会自动加载。想手动加载，输入：

```
/building-with-typesafe-jev:building-with-typesafe-jev
```

</details>

<details>
<summary><strong>Claude Desktop、Cowork 和 claude.ai</strong></summary>

打开 **Customize > Plugins > Add > Add marketplace**，选择 **Add from a repository**，输入 `aaddrick/building-with-typesafe-jev`。保持 **Sync automatically** 开启，插件会随本仓库一起更新。选择 **Sync**，然后选择 **Building with typesafe jev** 旁边的 **Add**。

</details>

<details>
<summary><strong>Codex</strong></summary>

```bash
codex plugin marketplace add aaddrick/building-with-typesafe-jev
```

```bash
codex plugin add building-with-typesafe-jev@building-with-typesafe-jev
```

开启一个新线程。任务匹配时，Codex 会加载这个技能。想手动加载，输入：

```
$building-with-typesafe-jev:building-with-typesafe-jev
```

</details>

<details>
<summary><strong>Antigravity CLI</strong></summary>

```bash
agy plugin install https://github.com/aaddrick/building-with-typesafe-jev
```

检查是否已安装：

```bash
agy plugin list
```

开启一个新会话。任务匹配时，Antigravity CLI 会加载这个技能。想手动加载，输入：

```
/building-with-typesafe-jev:building-with-typesafe-jev
```

从 Gemini CLI 迁移过来？如果 `agy plugin import gemini` 已经导入了这个扩展，也请运行上面的安装命令，用当前版本替换导入的副本。

</details>

<details>
<summary><strong>Muse (muse.ai)</strong></summary>

Muse 从它自己电脑上的 `~/workspace/skills/` 加载技能。把这条命令粘贴到 Muse 对话里，让 Muse 运行它：

```bash
curl -fsSL https://raw.githubusercontent.com/aaddrick/building-with-typesafe-jev/main/scripts/install_muse.sh | bash
```

脚本会把技能文件夹复制到那里，并把 `SKILL.md` 的头部改写成 Muse 能读取的格式。开始一个新对话。任务匹配时，Muse 会加载这个技能。要更新，再运行一次这条命令。

</details>

<details>
<summary><strong>Muse Code</strong></summary>

克隆仓库：

```bash
git clone https://github.com/aaddrick/building-with-typesafe-jev.git
```

为所有项目安装这个技能：

```bash
muse skills install building-with-typesafe-jev/skills/building-with-typesafe-jev --scope user
```

检查是否安装成功：

```bash
muse skills list
```

开始一个新会话。任务匹配时，Muse Code 会加载这个技能。想手动加载，输入：

```
/building-with-typesafe-jev
```

</details>

<details>
<summary><strong>其他任何能读取 SKILL.md 的智能体</strong></summary>

把 `skills/building-with-typesafe-jev/` 文件夹复制到你的智能体的技能文件夹里。保留整个文件夹。`SKILL.md` 会链接到它旁边的文件。

</details>

## 设置 API 密钥（可选，推荐）

没有密钥，这个技能也能用。在智能体的 shell 中设置好 `TYPESAFE_API_KEY` 后，智能体可以在代码进入你的项目之前，用真实的 API 检查它的设计。这样能发现写错的字段名，以及 Jev 的理解与你本意不同的问题。每次调用的费用不到一美分。

<details>
<summary><strong>创建、保存密钥及排查问题</strong></summary>

<br>

<details>
<summary><strong>创建密钥</strong>（在 TypeSafe 控制台中分四步完成）</summary>

**第 1 步。** 登录 [console.typesafe.ai](https://console.typesafe.ai/)，在侧边栏中打开 **API Keys**。

<img src="../assets/api-key/step-1.png" alt="TypeSafe 控制台首页。一个琥珀色方框和箭头指向左侧边栏中的 API Keys。" width="100%">

**第 2 步。** 点击右上角的 **Create key**。

<img src="../assets/api-key/step-2.png" alt="API 密钥页面。已有的密钥被模糊处理。一个琥珀色方框和箭头指向右上角的 Create key 按钮。" width="100%">

**第 3 步。** 按密钥的使用位置给它命名，比如机器名或智能体名。然后点击 **Create key**。

<img src="../assets/api-key/step-3.png" alt="Create API key 对话框，名称栏中已输入 my-coding-agent。一个琥珀色方框和箭头指向名称栏和 Create key 按钮。" width="100%">

**第 4 步。** 现在就复制密钥。控制台只显示一次。如果弄丢了，就新建一个，并撤销旧的。

<img src="../assets/api-key/step-4.png" alt="API key created 对话框。密钥值被遮盖。一个琥珀色方框和箭头指向 Copy 按钮。" width="100%">

</details>

<details>
<summary><strong>保存密钥</strong>（macOS、Linux、Windows）</summary>

把密钥放在单独的文件里，并且只有你能读取，然后把它导出为 `TYPESAFE_API_KEY`。智能体经常在没有终端的情况下启动 shell，所以每一节都会把密钥放在这些 shell 能看到的地方。选择你的系统。

<details>
<summary><strong>macOS</strong>（zsh，默认 shell）</summary>

把密钥保存到私有文件：

```bash
mkdir -p ~/.config/typesafe && umask 077 && printf 'export TYPESAFE_API_KEY=%s\n' 'YOUR_KEY' > ~/.config/typesafe/env
```

从 `~/.zshenv` 加载它。每个 zsh 都会读取这个文件，包括智能体在没有终端时启动的 shell。`~/.zshrc` 只会被交互式 shell 读取。

```bash
echo '[ -f ~/.config/typesafe/env ] && . ~/.config/typesafe/env' >> ~/.zshenv
```

打开一个新终端检查一下。这条命令打印的是密钥的长度，而不是密钥本身：

```bash
echo ${#TYPESAFE_API_KEY}
```

</details>

<details>
<summary><strong>Linux 使用 bash</strong>（Ubuntu、Debian、Mint、Fedora、Arch）</summary>

把密钥保存到私有文件：

```bash
mkdir -p ~/.config/typesafe && umask 077 && printf 'export TYPESAFE_API_KEY=%s\n' 'YOUR_KEY' > ~/.config/typesafe/env
```

在 `~/.bashrc` 的**顶部**加载它。Ubuntu、Debian、Mint 和 Arch 的 `~/.bashrc` 开头有一行，会在没有连接终端时提前退出。写在这道检查下面的行永远不会为智能体的 shell 执行。文件顶部在每个发行版上都是安全的：

```bash
sed -i '1i [ -f ~/.config/typesafe/env ] \&\& . ~/.config/typesafe/env' ~/.bashrc
```

打开一个新终端检查一下：

```bash
echo ${#TYPESAFE_API_KEY}
```

</details>

<details>
<summary><strong>Linux 使用 zsh</strong></summary>

按照 macOS 的步骤操作。zsh 在 Linux 上也以同样的方式读取 `~/.zshenv`。

</details>

<details>
<summary><strong>Linux 使用 fish</strong></summary>

fish 会读取 `~/.config/fish/conf.d/` 中的每个文件，无论有没有终端：

```fish
mkdir -p ~/.config/fish/conf.d; and echo 'set -gx TYPESAFE_API_KEY YOUR_KEY' > ~/.config/fish/conf.d/typesafe.fish; and chmod 600 ~/.config/fish/conf.d/typesafe.fish
```

```fish
string length -- $TYPESAFE_API_KEY
```

</details>

<details>
<summary><strong>Windows</strong>（PowerShell）</summary>

把密钥保存为用户环境变量。新打开的终端和应用能看到它，已经打开的终端看不到：

```powershell
[Environment]::SetEnvironmentVariable('TYPESAFE_API_KEY', 'YOUR_KEY', 'User')
```

打开一个新终端检查一下：

```powershell
$env:TYPESAFE_API_KEY.Length
```

**WSL：** 默认情况下，Windows 变量不会传到 WSL 中。在 WSL 里，请按照 Linux 使用 bash 的步骤操作。

</details>

<details>
<summary><strong>桌面应用和 IDE 扩展</strong></summary>

从程序坞、开始菜单或桌面启动器打开的应用不会读取你的 shell 文件。

- **Windows：** 上面设置的用户环境变量已经覆盖了这些应用。
- **Linux（systemd）：** 把 `TYPESAFE_API_KEY=YOUR_KEY` 这一行加入 `~/.config/environment.d/typesafe.conf`，然后注销并重新登录。
- **macOS：** 从终端启动应用，或者在应用自己的设置中设置这个变量。macOS 没有简单的、桌面应用会读取的按用户配置文件。

</details>

</details>

<details>
<summary><strong>如果智能体看不到密钥</strong></summary>

让智能体运行 `echo ${#TYPESAFE_API_KEY}`（在 Windows 上是 `$env:TYPESAFE_API_KEY.Length`）。如果它打印出 `0` 或什么都没打印，按顺序检查以下几项：

- **你在保存密钥之前就启动了智能体。** 智能体的 shell 会复制启动它的程序的环境。退出智能体，然后从一个新终端启动它。
- **你从程序坞、开始菜单或 IDE 启动了智能体。** 这些应用不会读取你的 shell 文件。参见上面的"桌面应用和 IDE 扩展"。
- **Codex 过滤了环境变量。** 如果 `~/.codex/config.toml` 在 `[shell_environment_policy]` 下设置了 `include_only`，把 `TYPESAFE_API_KEY` 加进去。如果它设置了 `ignore_default_excludes = false`，Codex 会丢弃名字中带有 `KEY` 的所有变量。删掉那一行。
- **WSL。** Windows 变量不会传到 WSL 中。按照 Linux 的步骤在 WSL 里保存密钥。

</details>

</details>

## 如何测试的

我们给一个编程智能体六个 Jev 任务，比如一个工单分诊函数和一个 shell 命令的审批闸门。每个任务在有这个技能、没有技能和有官方技能三种设置下各运行 10 次，每一组都在各自隔离的容器中运行。智能体有文档，但没有 API 密钥，所以评分者检查的是它写出的代码。需要判断的检查项交给来自三家提供商的三个 LLM 评判模型（Claude Opus、GPT-6 Sol、Kimi K3），按多数决定。

| | 没有技能 | 这个技能 | 官方技能 |
|---|---:|---:|---:|
| 平均得分 | 0.65 ± 0.05 | **0.96 ± 0.02** | 0.77 ± 0.04 |

得分是通过的检查项所占的比例，按每个任务 10 次运行取平均。

**这个技能带来差别的地方**（10 次运行中通过的次数）：

| 智能体的代码…… | 没有技能 | 这个技能 | 官方技能 |
|---|---:|---:|---:|
| 在代码里计数，而不是让 Jev 给出一个数字 | 1 | 8 | 0 |
| 在问题中点名输入里的某个字段 | 0 | 10 | 1 |
| 固定或记录了 Jev 的模型版本 | 0 | 10 | 0 |
| 给部门列表加上一个兜底选项 | 3 | 10 | 6 |
| 遍历 1,200 个类别时保留不止一条路径 | 1 | 10 | 7 |
| 为破坏性命令保留一条普通代码的兜底规则 | 7 | 10 | 2 |
| 把 `score` 读作从 0 到 n-1 的位置 | 9 | 10 | 5 |

[查看每一项检查 →](../../evals/docs/results.md#every-check)

在 95% 置信度下，表中每一行都胜过没有技能、官方技能或两者，差距超出偶然范围。

**更多细节：**

- [evals/README.md](../../evals/README.md)：按用例列出的结果，以及如何运行这套评测
- [evals/docs/results.md](../../evals/docs/results.md)：每一项检查、每个评判模型的评分、费用、token 和方法
- [evals/docs/cases.md](../../evals/docs/cases.md)：六个任务，以及每项检查看的是什么
- [evals/docs/harness.md](../../evals/docs/harness.md)：一次运行如何进行、隔离容器，以及如何保留一批评测结果
- [evals/docs/lessons.md](../../evals/docs/lessons.md)：搭建这套评测时出过的问题

## 里面有什么

技能分层加载，智能体只读任务需要的部分。

| 文件 | 内容 | 智能体何时读取 |
|---|---|---|
| `SKILL.md` | 选哪种原语、11 条设计规则、如何使用概率和置信度、常见错误 | 每个 Jev 任务 |
| `api-reference.md` | HTTP API、Python 和 JavaScript SDK、限制、错误、环境变量 | 写代码时 |
| `patterns.md` | 4 种官方模式，以及来自 18 份 cookbook 的技巧和阈值 | 设计工作流时 |
| `prior-art/INDEX.md` | 从"我想做什么"到形态的映射，以及失败过的想法 | 设计新东西之前 |
| `prior-art/*.md` | 11 个形态文件：代码草图、实战经验和相关项目链接 | 每次设计读一两个 |

## 先例库

大多数目录按行业给项目分类。这个库按实现形态分类。游戏机器人、无人机和交易机器人是同一种形态：控制循环。这样分类后，三者共用一份代码草图和一套实战经验。11 种形态如下：

- **[控制循环](../../skills/building-with-typesafe-jev/prior-art/control-loops.md)**：游戏、无人机、机器人、市场。
- **[从候选中选择](../../skills/building-with-typesafe-jev/prior-art/select-from-candidates.md)**：浏览器和手机智能体、不用 LLM 的工具调用、信息抽取、路由器。
- **[闸门](../../skills/building-with-typesafe-jev/prior-art/gates.md)**：工具调用审批、"完成"检查、CI、资金、内容。
- **[流过滤](../../skills/building-with-typesafe-jev/prior-art/stream-filters.md)**：垃圾内容过滤、内容审核、邮件、日志、批量标注。
- **[排序与匹配](../../skills/building-with-typesafe-jev/prior-art/ranking-and-matching.md)**：重排序器、实体匹配、图和分类体系遍历。
- **[评判与评估](../../skills/building-with-typesafe-jev/prior-art/judges-and-evals.md)**：基于评分标准的评判、轨迹评分、把代码审查当作分诊。
- **[增量与实时](../../skills/building-with-typesafe-jev/prior-art/incremental-realtime.md)**：配音、语音、由按键驱动的界面。
- **[智能体上下文与记忆](../../skills/building-with-typesafe-jev/prior-art/agent-context-memory.md)**：压缩、记忆闸门、记忆过期、投入度控制。
- **[与 LLM 搭配](../../skills/building-with-typesafe-jev/prior-art/llm-pairing.md)**：规划者与执行者、先验证再升级、蒸馏。
- **[把答案当数据](../../skills/building-with-typesafe-jev/prior-art/research-and-features.md)**：经典模型的特征、研究工具、基准测试。
- **[嵌入基础设施](../../skills/building-with-typesafe-jev/prior-art/embedding-in-infrastructure.md)**：SQL 函数、向量数据库、CI 钩子、Home Assistant。

索引还列出了在实战中失败的想法：国际象棋、把代码审查当作唯一审查者、感知任务，以及不加验证就相信校准。一次失败的尝试，能让下一个开发者不必重蹈覆辙。

## 与官方技能的区别

[TypeSafe 官方技能](https://github.com/typesafe-ai/skills)是一个只包含设计指导的文件。涉及 API 细节时，它会在每个任务中让智能体去读线上文档。两个技能名称不同，互不冲突，所以你可以两个都安装，不过评估没有测试过两者同时安装的情况。

这个技能本身包含更多内容：确切的 API 结构、cookbook 里的阈值、社区总结的失败模式，以及先例库。智能体不用联网就能做设计，也能先看到别人已经做过什么。

Jev 变化很快。这个技能是 2026-09-25 时 [docs.typesafe.ai](https://docs.typesafe.ai/llms.txt) 和社区状况的快照，它告诉智能体，出现冲突时以线上文档为准。如果有事实错误，请提交 issue 并附上来源链接。

## 致谢

关于 API 的事实来自 TypeSafe AI 的公开文档和 cookbook。先例来自发布了自己项目的开发者、Hacker News 社区，以及这些索引：[awesome-jev-typesafe](https://github.com/valentynkit/awesome-jev-typesafe)、[JevDirectory](https://www.jevdirectory.org/resources)、[awesome-jev-use-cases](https://github.com/walidboulanouar/awesome-jev-use-cases) 和 [awesome-typesafe-jev](https://github.com/AbdelStark/awesome-typesafe-jev)。每个形态文件都链接到原始项目。

TypeSafe、Jev 和 System One 是 TypeSafe AI 的名称。本项目使用它们，只是为了说明这个技能的用途。

## 许可证

MIT。参见 [LICENSE](../../LICENSE)。
