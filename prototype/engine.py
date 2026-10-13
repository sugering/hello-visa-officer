"""《你好签证官》核心循环原型引擎。

架构约定（决定后续 Ren'Py 落地方式）
------------------------------------
* 引擎不依赖任何 UI 框架，只做状态机与数值判定；Ren'Py 侧只做渲染。
* 所有对外输出都是 **事件字典列表**（say / suspicion / probe / conflict / puzzle / ending），
  表现层照单渲染，引擎不知道立绘长什么样。
* 内容（材料、对话、谜题、结局阈值）全部外置 JSON，改内容不改代码。

核心循环：回合 → 选择话术或提交材料 → 签证官反应 → 怀疑度 / 一致性更新 → 终局判定。
"""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Dict, List, Optional

from puzzles import make_puzzle

CONTENT = Path(__file__).resolve().parent / "content"


def load_json(name: str) -> dict:
    with open(CONTENT / name, encoding="utf-8") as fh:
        return json.load(fh)


# --------------------------------------------------------------------------
# 数据结构
# --------------------------------------------------------------------------

@dataclass
class Material:
    id: str
    name: str
    category: str
    source: str            # genuine 真实 | modified 半真 | forged 伪造
    credibility: int       # 表面可信度 0-100（决定终局材料分）
    robustness: int        # 抗追问强度 0-100（低于追问压力就崩）
    facts: List[str] = field(default_factory=list)
    flaws: List[str] = field(default_factory=list)
    consumable: bool = False

    @property
    def forged(self) -> bool:
        return self.source == "forged"

    @property
    def source_label(self) -> str:
        return {"genuine": "真实", "modified": "半真", "forged": "伪造"}.get(self.source, self.source)


@dataclass
class Option:
    id: str
    text: str
    goto: Any = None
    requires: Dict[str, Any] = field(default_factory=dict)
    effects: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)


@dataclass
class Node:
    id: str
    speaker: str = "officer"
    text: str = ""
    mood: Optional[str] = None
    options: List[Option] = field(default_factory=list)
    puzzle: Optional[str] = None
    terminal: bool = False
    on_enter: Dict[str, Any] = field(default_factory=dict)


class OptionLocked(Exception):
    """选项条件不满足。"""


class InterviewOver(Exception):
    """面试已经结束。"""


# --------------------------------------------------------------------------
# 引擎
# --------------------------------------------------------------------------

class Interview:
    def __init__(self, materials: dict, dialogue: dict, scenario: dict,
                 puzzles: Optional[dict] = None) -> None:
        self.material_defs = {m["id"]: Material(**m) for m in materials["materials"]}
        self.contradictions = [tuple(pair) for pair in materials.get("contradictions", [])]
        self.node_defs = {nid: self._parse_node(nid, nd) for nid, nd in dialogue["nodes"].items()}
        self.start_node = dialogue["start"]
        self.scenario = scenario
        self.puzzle_defs = {p["id"]: p for p in (puzzles or {}).get("puzzles", [])}
        self.reset()

    @staticmethod
    def _parse_node(nid: str, nd: dict) -> Node:
        return Node(
            id=nid,
            speaker=nd.get("speaker", "officer"),
            text=nd.get("text", ""),
            mood=nd.get("mood"),
            options=[Option(**{**{"id": o["id"], "text": o["text"]}, **{k: v for k, v in o.items() if k not in ("id", "text")}}) for o in nd.get("options", [])],
            puzzle=nd.get("puzzle"),
            terminal=nd.get("terminal", False),
            on_enter=nd.get("on_enter", {}),
        )

    # ---- 生命周期 ----------------------------------------------------
    def reset(self) -> None:
        self.sheet: Dict[str, Material] = {}
        for mid in self.scenario["starting_materials"]:
            self.sheet[mid] = copy.deepcopy(self.material_defs[mid])
        self.owned: List[str] = list(self.sheet.keys())
        self.submitted: List[str] = []
        self.recorded_facts: List[str] = []   # 签证官已经读到的事实（来自材料）
        self.statements: List[str] = []        # 玩家嘴上说过的话
        self.exposed: set = set()              # 被追问击穿的材料
        self.consumed: set = set()
        self.flags: set = set()
        self.suspicion: int = self.scenario["starting_suspicion"]
        self.round: int = 0
        self.node_id: Optional[str] = self.start_node
        self.ended: Optional[str] = None
        self.verdict: Optional[dict] = None
        self.events: List[dict] = []
        self.forced_mood: Optional[str] = None
        self.solved_puzzles: set = set()
        self.last_probe_result: Optional[str] = None
        self.log: List[str] = []

    # ---- 渲染给表现层的信息 -----------------------------------------
    @property
    def node(self) -> Optional[Node]:
        return self.node_defs.get(self.node_id) if self.node_id else None

    @property
    def mood(self) -> str:
        """立绘表情，优先级：事件（击穿/矛盾/感兴趣）> 节点指定 > 怀疑度分档。

        分档是主要来源（玩家能通过脸读出自己离崩多远），节点指定留给导演式微调，
        事件覆盖用来给"被抓住"和"引起兴趣"两个高光时刻。
        """
        if self.forced_mood:
            return self.forced_mood
        node = self.node
        if node is not None and node.mood:
            return node.mood
        if self.suspicion >= 85:
            return "caught"
        if self.suspicion >= 45:
            return "impatient"
        if self.suspicion >= 20:
            return "doubt"
        return "calm"

    def node_events(self) -> List[dict]:
        """进入当前节点时要播的内容（包括触发弹窗解谜）。"""
        out: List[dict] = []
        node = self.node
        if node is None:
            return out
        if node.puzzle and node.puzzle not in self.solved_puzzles:
            out.append({"type": "puzzle", "id": node.puzzle,
                        "config": self.puzzle_defs.get(node.puzzle, {})})
        if node.text:
            out.append({"type": "say", "speaker": node.speaker,
                        "mood": self.mood, "text": node.text})
        return out

    def available_options(self) -> List[dict]:
        """返回所有选项及其可用性，UI 用 locked/reason 决定是否置灰。"""
        node = self.node
        if node is None:
            return []
        out = []
        for opt in node.options:
            ok, reason = self._check_requires(opt)
            out.append({"option": opt, "locked": not ok, "reason": reason,
                        "conflict_preview": self.preview_conflicts(opt)})
        return out

    def preview_conflicts(self, opt: Option) -> List[dict]:
        """选择前就能预判的冲突——UI 用它在选项上打 ⚠，这是"可读的策略"关键。"""
        hits = []
        for st in opt.effects.get("statements", []):
            for other in self.recorded_facts + self.statements:
                if self._is_conflict(st, other):
                    hits.append({"new": st, "with": other})
        return hits

    def snapshot(self) -> dict:
        return {
            "round": self.round,
            "round_limit": self.scenario["round_limit"],
            "suspicion": self.suspicion,
            "suspicion_limit": self.scenario["suspicion_limit"],
            "mood": self.mood,
            "node": self.node_id,
            "owned": [self._brief(mid) for mid in self.owned],
            "submitted": list(self.submitted),
            "submitted_detail": [self._brief(mid) for mid in self.submitted],
            "exposed": sorted(self.exposed),
            "flags": sorted(self.flags),
            "statements": list(self.statements),
            "ended": self.ended,
        }

    def _brief(self, mid: str) -> dict:
        m = self.sheet.get(mid)
        if m is None:
            return {"id": mid, "name": mid, "missing": True}
        return {"id": m.id, "name": m.name, "category": m.category, "source": m.source_label,
                "credibility": m.credibility, "robustness": m.robustness, "flaws": list(m.flaws)}

    # ---- 选择与结算 --------------------------------------------------
    def choose(self, option_id: str) -> List[dict]:
        if self.ended:
            raise InterviewOver(f"面试已结束：{self.ended}")
        node = self.node
        if node is None:
            raise InterviewOver("当前节点为空")
        opt = next((o for o in node.options if o.id == option_id), None)
        if opt is None:
            raise KeyError(f"节点 {node.id} 没有选项 {option_id}")
        ok, reason = self._check_requires(opt)
        if not ok:
            raise OptionLocked(f"{opt.id} 不可选：{reason}")

        events: List[dict] = [{"type": "player", "text": opt.text, "tags": list(opt.tags)}]
        self.forced_mood = None
        self.round += 1
        self._apply_effects(opt.effects, events)
        goto = self._resolve_goto(opt.goto, events)
        self.node_id = goto
        if self.node_id:
            enter = self.node_defs[self.node_id].on_enter
            self._apply_effects(enter, events)
            events.extend(self.node_events())
        self.log.append(f"R{self.round} {node.id}:{opt.id} → {goto} suspicion={self.suspicion}")
        self._check_ending(events)
        self.events = events
        return events

    def apply_puzzle_result(self, puzzle_id: str, solved: bool, moves: int,
                            payload: Optional[dict] = None) -> List[dict]:
        """表现层跑完弹窗解谜后回调。谜题结果只通过这里影响数值，接口收口在一处。"""
        cfg = self.puzzle_defs.get(puzzle_id)
        if cfg is None:
            raise KeyError(f"未知谜题 {puzzle_id}")
        budget = cfg.get("move_budget", 99)
        if not solved:
            key = "on_fail"
        elif moves <= budget:
            key = "on_solve_within_budget"
        else:
            key = "on_solve_over_budget"
        if solved:
            self.solved_puzzles.add(puzzle_id)
        events: List[dict] = [{"type": "puzzle_result", "id": puzzle_id, "solved": solved,
                               "moves": moves, "budget": budget, "tier": key}]
        reward = cfg.get("reward", {}).get(key, {})
        self._apply_effects(reward, events)
        # "整理文件"这类谜题的产物是玩家自己配出来的：把结算数值写进刚发放的材料
        if payload and reward.get("apply_payload"):
            for mid in reward.get("grant", []):
                m = self.sheet.get(mid)
                if m is None:
                    continue
                m.credibility = int(payload.get("credibility", m.credibility))
                m.robustness = int(payload.get("robustness", m.robustness))
                if "flaws" in payload:
                    m.flaws = list(payload["flaws"])
                events.append({"type": "material_graded", "material": self._brief(mid),
                               "credibility": m.credibility, "robustness": m.robustness,
                               "flaws": list(m.flaws)})
        self._check_ending(events)
        return events

    # ---- 条件与效果 --------------------------------------------------
    def _check_requires(self, opt: Option) -> tuple:
        req = opt.requires or {}
        for mid in req.get("materials", []):
            if mid not in self.owned:
                return False, f"缺少材料：{self.material_defs[mid].name if mid in self.material_defs else mid}"
        for flag in req.get("flags", []):
            if flag not in self.flags:
                return False, f"缺少前置条件：{flag}"
        for flag in req.get("not_flags", []):
            if flag in self.flags:
                return False, f"已触发过：{flag}"
        if "max_suspicion" in req and self.suspicion > req["max_suspicion"]:
            return False, f"怀疑度过高（{self.suspicion} > {req['max_suspicion']}）"
        return True, ""

    def _apply_effects(self, effects: dict, events: List[dict]) -> None:
        for st in effects.get("statements", []):
            self._add_statement(st, events)
        for mid in effects.get("submit", []):
            self._submit(mid, events)
        probe = effects.get("probe")
        probe_result = None
        if probe:
            probe_result = self._probe(probe, events)
        if "suspicion" in effects:
            self._shift_suspicion(effects["suspicion"], events, reason="对话影响")
        if effects.get("intrigue"):
            self.forced_mood = "interested"
        for mid in effects.get("grant", []):
            if mid not in self.sheet:
                self.sheet[mid] = copy.deepcopy(self.material_defs[mid])
            if mid not in self.owned:
                self.owned.append(mid)
            events.append({"type": "grant", "material": self._brief(mid)})
        for spec in effects.get("remove_flaws", []):
            mid, _, flaw = spec.partition(":")
            m = self.sheet.get(mid)
            if m and flaw in m.flaws:
                m.flaws.remove(flaw)
                m.robustness = min(100, m.robustness + 12)
                events.append({"type": "material_improved", "material": self._brief(mid), "removed_flaw": flaw})
        for flag in effects.get("flags", []):
            self.flags.add(flag)
        for flag in effects.get("not_flags", []):
            self.flags.discard(flag)
        for mid in effects.get("consume", []):
            if mid in self.owned:
                self.owned.remove(mid)
                self.consumed.add(mid)
        self.last_probe_result = probe_result

    def _resolve_goto(self, goto: Any, events: List[dict]) -> Optional[str]:
        if isinstance(goto, dict):
            result = getattr(self, "last_probe_result", None)
            if result and result in goto:
                return goto[result]
            return goto.get("default")
        return goto

    def _add_statement(self, st: str, events: List[dict]) -> None:
        for other in self.recorded_facts + self.statements:
            if self._is_conflict(st, other):
                self.flags.add("caught_lying")
                self.forced_mood = "caught"
                self._shift_suspicion(20, events, reason="陈述与材料矛盾")
                events.append({"type": "conflict", "statement": st, "with": other,
                               "note": "签证官翻了一下材料，把两页并排放在一起"})
                break
        self.statements.append(st)

    def _submit(self, mid: str, events: List[dict]) -> None:
        if mid not in self.sheet:
            return
        m = self.sheet[mid]
        if mid not in self.submitted:
            self.submitted.append(mid)
            events.append({"type": "submit", "material": self._brief(mid)})
        for fact in m.facts:
            for other in self.statements:
                if self._is_conflict(fact, other):
                    self.flags.add("caught_lying")
                    self.forced_mood = "caught"
                    self._shift_suspicion(20, events, reason="材料与陈述矛盾")
                    events.append({"type": "conflict", "statement": fact, "with": other,
                                   "note": f"{m.name}上的内容和你刚才的说法对不上"})
            if fact not in self.recorded_facts:
                self.recorded_facts.append(fact)
        if m.consumable and mid in self.owned:
            self.owned.remove(mid)
            self.consumed.add(mid)

    def _probe(self, mid: str, events: List[dict]) -> str:
        """追问判定：压力随怀疑度上升；抗性不足则击穿，破绽越多崩得越狠。"""
        m = self.sheet.get(mid)
        if m is None:
            return "hold"
        pressure = 30 + self.suspicion * 0.6
        result = "hold" if m.robustness >= pressure else "break"
        if result == "hold":
            self._shift_suspicion(-3, events, reason="材料顶住追问")
            events.append({"type": "probe", "material": self._brief(mid), "result": "hold",
                           "pressure": round(pressure, 1)})
        else:
            self.exposed.add(mid)
            self.flags.add(f"broke:{mid}")
            penalty = 10 + 5 * len(m.flaws)
            if m.forged:
                penalty += 5
            self.forced_mood = "caught"
            self._shift_suspicion(penalty, events, reason="材料被追问击穿")
            events.append({"type": "probe", "material": self._brief(mid), "result": "break",
                           "pressure": round(pressure, 1), "flaws": list(m.flaws),
                           "note": "签证官把材料转了个方向，指着上面那行字"})
        return result

    def _is_conflict(self, a: str, b: str) -> bool:
        if a == b:
            return False
        for x, y in self.contradictions:
            if {a, b} == {x, y}:
                return True
        return False

    def _shift_suspicion(self, delta: int, events: List[dict], reason: str = "") -> None:
        before = self.suspicion
        self.suspicion = max(0, min(999, self.suspicion + delta))
        events.append({"type": "suspicion", "delta": self.suspicion - before,
                       "value": self.suspicion, "reason": reason})

    # ---- 终局 --------------------------------------------------------
    def _check_ending(self, events: List[dict]) -> None:
        if self.ended:
            return
        if self.suspicion >= self.scenario["suspicion_limit"]:
            self._resolve_verdict(events, reason="suspicion_limit", forced="caught")
        elif "caught_lying" in self.flags and self.suspicion >= 60:
            self._resolve_verdict(events, reason="caught_lying", forced="caught")
        # 硬性时间约束优先于"聊完了"：回合耗尽时即使刚到裁决节点，也按超时记录
        elif self.round >= self.scenario["round_limit"]:
            self._resolve_verdict(events, reason="round_limit")
        elif self.node_id is None:
            self._resolve_verdict(events, reason="interview_complete")

    def _resolve_verdict(self, events: List[dict], reason: str, forced: Optional[str] = None) -> None:
        sc = self.scenario
        weights = sc["category_weights"]
        min_cred = sc.get("min_credibility_for_coverage", 50)
        good = [self.sheet[i] for i in self.submitted if i in self.sheet and i not in self.exposed]
        covered = {cat: max([m.credibility for m in good if m.category == cat], default=0)
                   for cat in sc["required_categories"]}
        coverage = sum(w for cat, w in weights.items() if covered.get(cat, 0) >= min_cred)
        quality = (sum(m.credibility for m in good) / len(good) / 100) if good else 0.0
        ties_ok = any(m.category == "ties" and m.credibility >= 60 for m in good)
        caught = "caught_lying" in self.flags
        bonus = (-15 if caught else 10) + (8 if ties_ok else 0)
        score = coverage * 70 + quality * 30 + bonus - 0.3 * self.suspicion

        thr = sc["verdict"]
        if forced:
            ending = forced
        elif score >= thr["pass_threshold"] and not caught and coverage >= 0.999:
            ending = "approved"
        elif score >= thr["review_threshold"]:
            ending = "administrative_review"
        else:
            ending = "denied"
        self.ended = ending
        self.verdict = {
            "ending": ending, "score": round(score, 1), "coverage": round(coverage, 3),
            "quality": round(quality, 3), "bonus": bonus, "suspicion": self.suspicion,
            "covered": covered, "missing": [c for c in sc["required_categories"] if covered.get(c, 0) < min_cred],
            "caught_lying": caught, "ties_ok": ties_ok, "reason": reason,
        }
        self.node_id = None
        events.append({"type": "ending", **self.verdict})

    # ---- 便捷入口 ----------------------------------------------------
    @classmethod
    def from_files(cls, scenario_file: str = "scenario.json",
                   dialogue_file: str = "dialogue.json",
                   materials_file: str = "materials.json",
                   puzzles_file: str = "puzzles.json") -> "Interview":
        return cls(load_json(materials_file), load_json(dialogue_file),
                   load_json(scenario_file), load_json(puzzles_file))
