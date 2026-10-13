# 原型 → Ren'Py 落地

> 原型已经把**玩法逻辑**跑通了（`prototype/engine.py`，14 个单元测试全绿）。
> 这一节只回答一件事：怎么把 UI 换成立绘 + 模态弹窗，而不重写逻辑。

## 1. 架构：一条明确的缝

```
┌─────────────────────────────┐        ┌──────────────────────────────┐
│  engine.py / puzzles.py     │        │  Ren'Py (game/*.rpy)         │
│  纯逻辑、零依赖、可离线测试  │        │  立绘、对话框、模态解谜、音效 │
│  输出：事件列表              │ ──────▶│  输入：事件 → 画面            │
│  输入：option_id / 解谜结果  │ ◀──────│                              │
└─────────────────────────────┘        └──────────────────────────────┘
        ↑ 只认这两个入口                      ↑ 从不直接改 suspicion
```

**换引擎（Godot / Web）时这套引擎原样复用**，只需要重写"事件 → 画面"那一侧。这是把原型做成纯 Python 而不是直接写 Ren'Py 脚本的核心理由。

## 2. 目录

```
hello-visa-officer/
├─ game/                   ← Ren'Py 项目
│  ├─ script.rpy           入口、路由
│  ├─ interview.rpy        对话循环 + 事件渲染
│  ├─ puzzle_lights_out.rpy 模态解谜 screen
│  ├─ screens_option.rpy   选项菜单（含置灰与 ⚠）
│  ├─ images/  audio/  fonts/
│  └─ options.rpy
├─ prototype/              ← 逻辑（被 game/ 引用）
│  ├─ engine.py  puzzles.py
│  └─ content/*.json
└─ docs/
```

## 3. 接线（`game/interview.rpy`）

```renpy
init python:
    import sys, os
    sys.path.insert(0, os.path.join(config.gamedir, "..", "prototype"))
    from engine import Interview
    from puzzles import make_puzzle

define officer = Character("签证官", color="#c8b48a")

default eng = None

label interview_start:
    $ eng = Interview.from_files()
    jump interview_loop

label interview_loop:
    $ render_events(eng.node_events())
    if eng.ended:
        jump verdict
    call screen option_menu(eng.available_options())
    $ render_events(eng.choose(_return))
    $ renpy.block_rollback()          # 引擎状态不可回滚，禁止玩家回退重选
    jump interview_loop
```

## 4. 事件渲染（工作量的 80% 在这一段）

```renpy
init python:
    MOOD_IMG = {
        "calm": "officer calm", "doubt": "officer doubt",
        "impatient": "officer impatient", "interested": "officer interested",
        "caught": "officer caught",
    }

    def render_events(events):
        for ev in events:
            kind = ev["type"]
            if kind == "say":
                renpy.show(MOOD_IMG.get(ev["mood"], "officer calm"))
                renpy.say(officer if ev["speaker"] == "officer" else None, ev["text"])
            elif kind == "player":
                renpy.say(None, "（{color=#888}%s{/color}）" % ev["text"])
            elif kind == "suspicion":
                renpy.play("audio/sfx/meter.ogg")
                renpy.restart_interaction()
            elif kind == "submit":
                renpy.play("audio/sfx/paper.ogg")
            elif kind == "probe":
                if ev["result"] == "break":
                    renpy.play("audio/sfx/break.ogg")
                    renpy.with_statement(hpunch)
            elif kind == "conflict":
                renpy.show_screen("conflict_popup", ev=ev)
                renpy.pause()
            elif kind == "puzzle":
                renpy.call_in_new_context("puzzle_" + ev["id"])
            elif kind == "ending":
                renpy.jump("verdict")
```

> 立绘用 `image officer calm = "characters/officer/officer_calm.png"` 定义，
> `MOOD_IMG` 的字符串就是 `mood` 事件字段，一一对应，不需要额外映射表。

## 5. 选项菜单（置灰 + ⚠ 预判）

```renpy
screen option_menu(options):
    vbox:
        for o in options:
            $ opt = o["option"]
            $ warn = " ⚠" if o["conflict_preview"] else ""
            textbutton opt.text + warn:
                sensitive not o["locked"]
                tooltip (o["reason"] if o["locked"] else "")
                action Return(opt.id)
        text "[eng.round] / [eng.scenario[round_limit]] 回合　怀疑度 [eng.suspicion]"
```

置灰理由直接来自引擎的 `locked / reason`，⚠ 来自 `conflict_preview` —— **表现层不做任何规则判断**，只显示引擎算好的结论。

## 6. 模态解谜（弹窗不打断沉浸感）

```renpy
label puzzle_seal_align:
    $ cfg = eng.puzzle_defs["seal_align"]
    $ board = make_puzzle(cfg["type"], cfg)
    call screen lights_out(board, cfg)
    $ render_events(eng.apply_puzzle_result("seal_align", board.is_solved(), board.move_count))
    return

screen lights_out(board, cfg):
    modal True
    add "ui/puzzle_backdrop.png"          # 半透明遮罩，签证官立绘透出来
    frame:
        xalign 0.5 yalign 0.5
        text cfg["flavor"]
        grid board.size board.size:
            for i in range(board.size * board.size):
                button:
                    xysize (120, 120)
                    background ("ui/tile_on.png" if board.cells[i] else "ui/tile_off.png")
                    action Function(board.toggle, i)
        text "[board.move_count] / [cfg[move_budget]] 步"
        textbutton "放弃" action Return()
```

要点：

- `modal True` + 全屏遮罩 = 立绘还在，但操作被锁在弹窗里（沉浸感的关键）。
- 谜题对象（`LightsOut`）是纯 Python，可以直接塞进 screen 的 `Function` action，不需要为 Ren'Py 改写。
- **只有 `apply_puzzle_result` 一个回调能改数值** —— 玩家重开弹窗、反复点，都不会污染状态。

## 7. 存档

- 引擎对象（`eng`）是普通 Python 对象，Ren'Py 的存档会自动 pickle 到 `store`；但**必须保证 `engine.py` 在存档时可 import**（路径固定，别改模块名）。
- 每次 `choose` 之后调用 `renpy.block_rollback()`：Ren'Py 的回滚会重放语句，而 `choose` 有副作用。
- 建议额外存一份 `eng.snapshot()` 的字典，用于存档缩略图与"上次玩到哪"的显示。

## 8. 测试策略

| 层 | 工具 | 频率 |
|---|---|---|
| 玩法逻辑 | `python -m unittest test_engine`（14 个用例） | 每次改数值都跑 |
| 路线回归 | `python run_demo.py good\|bluff\|bare`，比对结局与总分 | 每次改对话/材料都跑 |
| UI | Ren'Py lint（`renpy.sh <project> lint`）+ 人工试玩 | 每个里程碑 |

数值一旦被测试钉死，改平衡时**故意让测试失败**是好事 —— 说明你确实改变了玩法，而不是改了没生效。

## 9. 落地顺序（建议 3–4 天）

1. 装 Ren'Py SDK；`renpy.sh <sdk> create_project hello-visa-officer`
2. 把 `prototype/` 拷进项目，跑通 `interview_start → 结局` 的纯文字流程（0.5 天）
3. 接立绘：先用占位色块/免费素材，5 个表情切换（0.5 天）
4. 做选项菜单（置灰 + ⚠）与怀疑度计（0.5 天）
5. 做模态解谜 screen（0.5–1 天）
6. 音效 + 结局图章演出（0.5 天）
7. 打包：`renpy.sh <sdk> launcher distribute hello-visa-officer` → Windows/Linux/macOS 三端

做完 1–5 就是一个**可试玩的垂直切片**：一个有立绘、有解谜、有分支、有结局的完整关卡。

## 10. 什么时候该换 Godot

只有在下面这些需求出现时才值得换：实时动作、复杂 3D、需要联网对战、或者要把解谜做成带物理的重度玩法。
纯视觉小说 + 弹窗小游戏，Ren'Py 的模态 screen 与文本系统比 Godot 省一半以上工作量。
