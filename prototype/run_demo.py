"""终端驱动：把脚本化路线跑一遍，打印完整事件流。

用途
----
1. 验证核心循环（材料 → 陈述 → 怀疑度 → 终局）真的能跑通；
2. 展示"引擎产出事件、表现层负责渲染"的接缝长什么样 ——
   Ren'Py 版就是把 render_event() 换成 screen，引擎一行不用改。

运行： python run_demo.py [good|bluff|bare]
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from engine import Interview           # noqa: E402
from puzzles import make_puzzle        # noqa: E402

MOOD_LABEL = {
    "calm": "平静审视", "doubt": "轻微怀疑", "impatient": "明显不耐烦",
    "interested": "突然感兴趣", "caught": "冷笑 / 识破",
}
SPEAKER_LABEL = {"officer": "签证官", "narrator": "旁白"}

# 三条脚本化路线：分别是"有备而来""靠嘴硬""手里没东西"
ROUTES = {
    "good": ["hand_over", "state_conference", "cite_bank", "resubmit_clean",
             "cite_job", "wait_result"],
    "bluff": ["hand_over", "state_tourism", "cite_company", "joke", "wait_result"],
    "bare": ["wait_silent", "state_tourism", "vague", "joke", "wait_result"],
}


def render_event(ev: dict) -> str:
    kind = ev["type"]
    if kind == "player":
        return f"  ▶ 你：{ev['text']}"
    if kind == "say":
        who = SPEAKER_LABEL.get(ev["speaker"], ev["speaker"])
        mood = MOOD_LABEL.get(ev.get("mood", ""), ev.get("mood", ""))
        return f"  【{who}·{mood}】{ev['text']}"
    if kind == "suspicion":
        return f"    · 怀疑度 {ev['delta']:+d} → {ev['value']}（{ev['reason']}）"
    if kind == "submit":
        m = ev["material"]
        return f"    · 递交《{m['name']}》 可信度{m['credibility']} 抗性{m['robustness']} 来源:{m['source']}"
    if kind == "probe":
        m = ev["material"]
        if ev["result"] == "hold":
            return f"    · 追问《{m['name']}》（压力{ev['pressure']}）→ 顶住"
        return (f"    · 追问《{m['name']}》（压力{ev['pressure']}）→ 被击穿，"
                f"破绽：{'、'.join(ev['flaws']) or '无'}\n    · {ev.get('note','')}")
    if kind == "conflict":
        return f"    · ⚠ 矛盾：你说「{ev['statement']}」，材料写「{ev['with']}」\n    · {ev.get('note','')}"
    if kind == "grant":
        return f"    · 获得材料《{ev['material']['name']}》"
    if kind == "material_improved":
        return f"    · 《{ev['material']['name']}》被修补，破绽「{ev['removed_flaw']}」消失"
    if kind == "puzzle":
        return f"    · ▣ 弹出解谜：{ev['config'].get('name', ev['id'])} —— {ev['config'].get('flavor','')}"
    if kind == "puzzle_result":
        return f"    · 解谜结果：{'完成' if ev['solved'] else '失败'}，{ev['moves']}/{ev['budget']} 步（{ev['tier']}）"
    if kind == "ending":
        return ("\n  ── 裁决 ──\n"
                f"  结局：{ev['ending']}｜总分 {ev['score']}（覆盖 {ev['coverage']} × 70 + "
                f"质量 {ev['quality']} × 30 + 修正 {ev['bonus']:+d} − 怀疑 {ev['suspicion']} × 0.3）\n"
                f"  缺项：{'、'.join(ev['missing']) or '无'}｜说漏嘴：{'是' if ev['caught_lying'] else '否'}"
                f"｜回国约束：{'有' if ev['ties_ok'] else '无'}｜触发：{ev['reason']}")
    return f"    · {ev}"


def play(route_name: str) -> Interview:
    script = ROUTES[route_name]
    eng = Interview.from_files()
    lines = [f"=== 路线 {route_name}：{' → '.join(script)} ==="]

    def flush(events):
        for ev in events:
            lines.append(render_event(ev))
            if ev["type"] == "puzzle":
                board = make_puzzle(ev["config"]["type"], ev["config"])
                lines.append("    初始棋盘：\n" + "\n".join("      " + r for r in board.render().splitlines()))
                solution = board.solve()
                board.apply(solution)
                lines.append(f"    （原型自动求解：点击 {solution}）")
                lines.extend(render_event(e) for e in eng.apply_puzzle_result(
                    ev["id"], board.is_solved(), board.move_count))

    flush(eng.node_events())
    for option_id in script:
        if eng.ended:
            break
        flush(eng.choose(option_id))
        snap = eng.snapshot()
        lines.append(f"  —— 回合 {snap['round']}/{snap['round_limit']}，"
                     f"怀疑度 {snap['suspicion']}/{snap['suspicion_limit']}，"
                     f"立绘：{MOOD_LABEL[snap['mood']]}")
    return eng, lines


if __name__ == "__main__":
    route = sys.argv[1] if len(sys.argv) > 1 else "good"
    eng, lines = play(route)
    text = "\n".join(lines)
    # Windows 控制台编码不可靠，正文以 UTF-8 落盘为准
    out_dir = Path(__file__).resolve().parent / "out"
    out_dir.mkdir(exist_ok=True)
    (out_dir / f"demo_{route}.txt").write_text(text + "\n", encoding="utf-8")
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    print(text)
    print(f"\n[已写出 out/demo_{route}.txt]")
