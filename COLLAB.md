# 双 agent 协作协议（DeepSeek ↔ Gemini）

> 目标：让「我（DSH 里的 DeepSeek）」和「你订阅档里的 Gemini」在同一个项目上分工干活，
> 且**不需要买 API**、不需要逆向 Google 的内部协议。

## 0. 先说结论：实测边界（2026-10-13）

| 路径 | 实测结果 |
|---|---|
| Gemini API（`generativelanguage.googleapis.com`） | **网络可达**：裸请求返回 `403 Method doesn't allow unregistered callers … Please use API Key`。**缺的只是一把 key**，订阅档不提供。 |
| 后台的 Gemini 桌面版（`Gemini.exe` v1.14.0，3 个进程） | **没有本地 API 端口**（netstat 里查不到它持有的监听端口），无法从外部调用。 |
| Antigravity 的 `agentapi` | **存在且有真接口**：`new-conversation [--model=flash_lite|flash|pro]`、`send-message`、`get-conversation-metadata`。但需要 `ANTIGRAVITY_LS_ADDRESS`，而 `language_server.exe` 独立启动会被它自己拒绝：`Failed to read initial metadata from stdin` —— 它要 IDE 通过 stdin 做握手，不是给外部脚本用的。继续逆向不划算。 |
| Windows 凭据 / `~/.gemini` / `~/.dsh` | 只有 DeepSeek 的凭据，**没有任何 Google 凭据或 `AIza…` key**。 |

**所以：不做"后台对后台"的直连，改成"共享工作区 + 文件交接"。** 这不需要任何破解，
而且比 API 直连更适合"一个出图、一个写代码"的分工 —— 图片和代码本来就得落到磁盘上。

## 1. 分工

| 角色 | 谁 | 负责 | 写哪些文件 |
|---|---|---|---|
| **工程侧** | 我（DeepSeek，DSH 会话） | 玩法逻辑、内容数据、测试、数值平衡、Ren'Py 接线 | `prototype/**`、`docs/**`、`game/**` |
| **美术/文案侧** | Gemini（Antigravity 或 Gemini 应用） | 出图与选图、表情一致性、英文文案润色、数值与文案的旁观评审 | `assets/**`、`for-gemini/out/**` |

## 2. 三种通道（按推荐顺序）

### A. 共享工作区（推荐）
在 **Antigravity** 里直接打开这个仓库的根目录。
Gemini 就能读到 `docs/` 与 `prototype/`，产出直接写进 `assets/`。
两个 agent 操作同一份文件系统，不需要任何桥接代码 —— 这是我们最接近"实时协作"的方式。

### B. 文件交接（异步）

`for-gemini/` 里是**为 Gemini 准备好的全部提示词包**（中文说明 + 英文出图提示，可整段复制）：

| 文件 | 内容 |
|---|---|
| `for-gemini/prompts.md` | 绘图：签证官 5 表情、3 背景、6 张材料道具、UI 套件、交付对照表 |
| `for-gemini/voice.md` | 配音：声音设定卡、TTS 提示词模板、试音稿、交付规范 |
| `for-gemini/voice-lines.csv` | 逐句台本（7 句 / 115 字，含语气与语速提示） |
| `for-gemini/bgm-sfx.md` | BGM 生成提示词 + 音效搜索关键词 |

- 我写任务与提示词 → `for-gemini/`
- Gemini 的产出 → `for-gemini/out/` 或 `assets/`
- 每完成一项，在本文档第 4 节的任务板加一行

### C. 人工转述
`for-gemini/prompts.md` 里的内容是**可以直接整段复制**的，粘进 Gemini 应用或网页版即可。

## 3. 防冲突规则（双方都必须遵守）

1. **同一文件同一时间只有一个作者**。我改 `prototype/` 和 `docs/`；Gemini 只写 `assets/` 和 `for-gemini/out/`。
2. **数值的唯一真源是 `prototype/content/*.json`**。Gemini 可以提修改建议（写进 `for-gemini/out/`），但不直接改这些 JSON —— 它们被 14 个单元测试钉着，改坏了 CI 会红。
3. **资产命名 = 内容 id**：细节见 `docs/01-资产清单与预算.md` 第 7 节。
4. 每次交接都在任务板上留一行，谁接手谁改状态。

## 4. 任务板

| id | 任务 | 负责 | 输入 | 产出位置 | 状态 |
|---|---|---|---|---|---|
| T1 | 签证官 5 表情 + 3 张背景的出图提示词 | 我 | `docs/01` | `for-gemini/prompts.md` | ✅ 完成 |
| T2 | 签证官 5 张表情差分 | Gemini | `for-gemini/prompts.md` | `assets/characters/officer/` | 🟡 初版完成（impatient 需重出全分辨率） |
| T3 | 面试室 / 文件整理室 / 使馆走廊 3 张背景 | Gemini | 同上 | `assets/backgrounds/` | ✅ 完成 |
| T4 | 评审玩法数值是否"感觉不公平"（读 `docs/03` 与测试用例） | Gemini | `docs/03`、`prototype/test_engine.py` | `for-gemini/out/review-balance.md` | ⬜ 待做 |
| T5 | 把关卡文案从中文母本润色为对外展示版 | Gemini | `prototype/content/dialogue.json` | `for-gemini/out/dialogue-polished.md` | ⬜ 待做 |
| T6 | **可玩逻辑测试 Demo**（tkinter 外壳 + 无头流程回归） | 我 | `demo/` | `demo/` | ✅ 完成 |
| T13 | 决定要不要再花一轮做 Ren'Py 版（发行用，见 `docs/04`） | 你 | `docs/04`、`demo/` | `game/` | ⬜ 待定 |
| T14 | **整理文件玩法**（可信度 × 破绽的取舍 + 账目耦合） | 我 | `docs/03` §7 | `prototype/puzzles.py`、`demo/` | ✅ 完成 |
| T7 | 6 张材料道具图 | Gemini | `for-gemini/prompts.md` 第 4 节 | `assets/items/` | 🟡 初版完成（流水「整理版」需重出） |
| T8 | UI 套件（对话框 / 按钮 / 怀疑度计 / 卡牌 / 解谜框 / 图章） | Gemini | 同上 第 5 节 | `assets/ui/` | 🟡 已抠出透明 PNG（下批请直接导 PNG） |
| T9 | 配音（**暂停**：先不做，台本已备好在 `for-gemini/voice-lines.csv`） | 你 / Gemini | `for-gemini/voice.md` | `assets/audio/voice/` | ⏸ 暂停 |
| T10 | BGM 4 首 + 音效 12 个 | 你 | `for-gemini/bgm-sfx.md` | `assets/audio/` | ⬜ 待做 |
| T11 | 台词改动后重跑台本导出 | 我 | `prototype/export_voice_lines.py` | `for-gemini/voice-lines.csv` | ✅ 已可用 |
| T12 | 按返工清单重出 3 项、微调 3 项 | Gemini | `for-gemini/prompts.md` 第 7 节 | `assets/` | ⬜ 待做 |

## 5. 给 Gemini 的启动提示词（整段复制）

```
你现在在这个仓库的根目录里工作。这是一个中文视觉小说游戏《你好签证官》，
玩法是「弹窗解谜 → 获得/修补材料 → 用材料支撑话术 → 在有限回合内糊弄签证官」。

分工：另一个 AI（DeepSeek）负责玩法逻辑、内容数据和测试，你负责美术出图、文案润色与旁观评审。
请不要修改 prototype/ 和 docs/ 下的文件；你的产出写到 assets/ 或 for-gemini/out/。

请先读这三个文件，再开始干活：
1. docs/01-资产清单与预算.md —— 资产规格、命名规范、成本
2. for-gemini/prompts.md —— 全部出图提示词（签证官 5 表情 + 3 背景 + 6 张材料道具 + UI 套件）
3. for-gemini/voice.md —— 配音提示词、试音稿与交付规范
4. docs/03-材料系统设计.md —— 玩法数值，用于评审任务

当前优先任务：T2（签证官 5 张表情差分）。
要求：先生成 calm，满意后把它作为参考图派生其余 4 张，只改表情不改人；
交付 PNG-24 透明底、2160×2160、命名 officer_calm.png / officer_doubt.png / officer_impatient.png / officer_interested.png / officer_caught.png，
放到 assets/characters/officer/。做完在 COLLAB.md 的任务板把 T2 标成完成。
```

## 6. 如果以后要真·直连

任意一条满足即可，都不贵：

1. **一个 Gemini API key**（AI Studio 免费档足够）→ 我把 `prototype/` 的文案校对、素材描述批量生成接到 API 上，甚至注册成 DSH 的 provider 让 subagent 直接跑 Gemini。
2. **Antigravity 官方支持的 CLI/插件通道**（例如它的 MCP 挂点 `~/.gemini/config/mcp_config.json` 目前是空的）→ 如果哪天它对外暴露稳定接口，我可以再探一次。
3. 订阅档若开放 **Code Assist / Cloud Code** 的本地代理，也可以走那条路。

在此之前，"共享工作区"是性价比最高的协作方式。
