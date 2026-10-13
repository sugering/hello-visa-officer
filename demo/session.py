"""游戏会话状态机 —— 零 GUI 依赖。

把"下一步显示什么、点击该发生什么"从 tkinter 外壳里剥出来之后，
整套流程可以在没有显示器的情况下跑自动化测试（见 demo/test_flow.py）。
tkinter 外壳只剩"把帧贴到 Canvas 上、把鼠标坐标翻译成逻辑坐标"。

规则一律由 prototype/engine.py 决定，这里不做任何玩法判断。
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "prototype"))

import layout                                          # noqa: E402
from engine import Interview                           # noqa: E402
from puzzles import make_puzzle                        # noqa: E402
from layout import desk_geometry                        # noqa: E402
from theme import OPTION, PUZZLE_FRAME, SCREEN, TILE, TILE_GAP   # noqa: E402

SPEAKER_LABEL = {"officer": "签证官", "narrator": ""}


def describe(ev: dict) -> str:
    """把机制类事件翻成一行中文，显示在对话框底部。"""
    t = ev["type"]
    if t == "suspicion":
        return f"怀疑度 {ev['delta']:+d} → {ev['value']}（{ev['reason']}）"
    if t == "probe":
        if ev["result"] == "hold":
            return "追问《%s》→ 顶住（压力 %.0f）" % (ev["material"]["name"], ev["pressure"])
        return "追问《%s》→ 被击穿：%s" % (ev["material"]["name"], "、".join(ev["flaws"]))
    if t == "conflict":
        return f"⚠ 矛盾：{ev['statement']} 与材料里的 {ev['with']} 对不上"
    if t == "submit":
        return f"递交《{ev['material']['name']}》"
    if t == "grant":
        return f"获得《{ev['material']['name']}》"
    if t == "material_improved":
        return f"修补《{ev['material']['name']}》：破绽「{ev['removed_flaw']}」消失"
    if t == "material_graded":
        m = ev["material"]
        return (f"整理完成《{m['name']}》：可信度 {ev['credibility']}　"
                f"抗性 {ev['robustness']}　破绽 {len(ev['flaws'])}")
    if t == "puzzle_result":
        return "解谜%s（%d/%d 步）" % ("完成" if ev["solved"] else "放弃", ev["moves"], ev["budget"])
    return ""


class Session:
    """一局面试。状态只有四种：line（看台词）/ choice（选话术）/ puzzle（弹窗）/ ending（裁决）。"""

    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.eng = Interview.from_files()
        self.queue = list(self.eng.node_events())
        self.log: list = []
        self.page = None
        self.last_page = ("签证官", "")
        self.options: list = []
        self.state = "line"
        self.board = None
        self.puzzle_cfg = None
        self.verdict = None
        self.desk_hover = None
        self.pump()

    # ---- 事件队列 ----------------------------------------------------
    def pump(self) -> None:
        while self.queue:
            ev = self.queue.pop(0)
            t = ev["type"]
            if t == "say":
                self.page = (SPEAKER_LABEL.get(ev["speaker"], ev["speaker"]), ev["text"])
                self.last_page = self.page
                self.state = "line"
                return
            if t == "player":
                self.page = ("你", ev["text"])
                self.last_page = self.page
                self.state = "line"
                return
            if t == "puzzle":
                self.puzzle_cfg = ev["config"]
                self.board = make_puzzle(ev["config"]["type"], ev["config"])
                self.state = "desk" if self.puzzle_cfg["type"] == "patch_statement" else "puzzle"
                return
            line = describe(ev)
            if line:
                self.log.append(line)
        self.page = None
        if self.eng.ended:
            self.verdict = self.eng.verdict
            self.state = "ending"
        else:
            self.options = self.eng.available_options()
            self.state = "choice"

    def advance(self) -> None:
        if self.state == "line":
            self.pump()

    # ---- 几何（给外壳做命中测试，也给测试算点击坐标） ----------------
    def option_rects(self):
        x, w, h, gap, top = OPTION["x"], OPTION["w"], OPTION["h"], OPTION["gap"], OPTION["top"]
        return [(x, top + i * (h + gap), w, h) for i in range(len(self.options[:3]))]

    def desk_choice_rect(self, slot_index: int, which: str):
        _p, rows, _s, _k = desk_geometry(len(self.board.slots))
        return rows[slot_index][which]

    def desk_submit_rect(self):
        return desk_geometry(len(self.board.slots))[2]

    def desk_skip_rect(self):
        return desk_geometry(len(self.board.slots))[3]

    def cell_rects(self):
        if self.board is None or not hasattr(self.board, "cells"):
            return []
        n = self.board.size
        gw = n * TILE + (n - 1) * TILE_GAP
        fx = (SCREEN[0] - PUZZLE_FRAME[0]) // 2
        fy = (SCREEN[1] - PUZZLE_FRAME[1]) // 2
        gx, gy = fx + (PUZZLE_FRAME[0] - gw) // 2, fy + 200
        return [(gx + c * (TILE + TILE_GAP), gy + r * (TILE + TILE_GAP), TILE, TILE)
                for r in range(n) for c in range(n)]

    def give_up_rect(self):
        fx = (SCREEN[0] - PUZZLE_FRAME[0]) // 2
        fy = (SCREEN[1] - PUZZLE_FRAME[1]) // 2
        return (fx + PUZZLE_FRAME[0] - 260, fy + PUZZLE_FRAME[1] - 96, 170, 60)

    @staticmethod
    def _hit(rects, lx, ly):
        for i, (x, y, w, h) in enumerate(rects):
            if x <= lx <= x + w and y <= ly <= y + h:
                return i
        return None

    # ---- 交互 --------------------------------------------------------
    def on_click(self, lx: float, ly: float) -> None:
        if self.state == "line":
            self.advance()
        elif self.state == "choice":
            idx = self._hit(self.option_rects(), lx, ly)
            if idx is not None:
                self.choose(idx)
        elif self.state == "puzzle":
            if self._hit([self.give_up_rect()], lx, ly) is not None:
                self.finish_puzzle(False, 0)
                return
            idx = self._hit(self.cell_rects(), lx, ly)
            if idx is None:
                return
            self.board.toggle(idx)
            if self.board.is_solved():
                self.finish_puzzle(True, self.board.move_count)
        elif self.state == "desk":
            hit = self.desk_hit(lx, ly)
            if hit is None:
                return
            if hit == "skip":
                self.finish_puzzle(False, self.board.moves)
            elif hit == "submit":
                if self.board.is_solved():
                    self.finish_puzzle(True, self.board.moves, self.board.outcome())
                else:
                    self.log.append("单子还有没处理的行，先做决定再交")
            else:
                slot_id, which = hit
                self.board.pick(slot_id, which)

    def choose(self, idx: int) -> bool:
        """选中第 idx 个选项。返回是否真的推进了（被锁的选项不会推进）。"""
        if self.state != "choice" or idx >= len(self.options):
            return False
        opt = self.options[idx]
        if opt["locked"]:
            self.log.append(f"「{opt['option'].text}」不可选：{opt['reason']}")
            return False
        self.queue = list(self.eng.choose(opt["option"].id))
        self.pump()
        return True

    def choose_by_text(self, needle: str) -> bool:
        for i, opt in enumerate(self.options):
            if needle in opt["option"].text and not opt["locked"]:
                return self.choose(i)
        return False

    def desk_hit(self, lx, ly):
        """返回 ("submit") 或 (slot_id, "safe"/"bold") 或 None。"""
        if self.state != "desk" or self.board is None:
            return None
        _panel, rows, submit, skip = desk_geometry(len(self.board.slots))
        if self._hit([submit], lx, ly) is not None:
            return "submit"
        if self._hit([skip], lx, ly) is not None:
            return "skip"
        for slot, rect in zip(self.board.slots, rows):
            for which in ("safe", "bold"):
                if self._hit([rect[which]], lx, ly) is not None:
                    return (slot["id"], which)
        return None

    def finish_puzzle(self, solved: bool, moves: int, payload=None) -> None:
        self.queue = list(self.eng.apply_puzzle_result(self.puzzle_cfg["id"], solved, moves, payload))
        self.board = None
        self.puzzle_cfg = None
        self.state = "line"
        self.pump()

    def solve_puzzle(self, policy: str = "balanced") -> bool:
        """自动过掉当前谜题（给回归测试和'提示'用）。

        整理流水用 balanced 策略：能占便宜的地方动手，但守住账目平衡。
        """
        if self.state == "desk":
            self.board.auto(policy)
            self.finish_puzzle(True, self.board.moves, self.board.outcome())
            return True
        if self.state != "puzzle":
            return False
        solution = self.board.solve()
        if solution is None:
            return False
        self.board.apply(solution)
        self.finish_puzzle(True, self.board.move_count)
        return True

    # ---- 渲染 --------------------------------------------------------
    def frame(self, hover_option=None, hover_cell=None, hover_desk=None):
        snap = self.eng.snapshot()
        if self.state == "desk":
            return layout.render(mood=snap["mood"], snapshot=snap, mode="desk",
                                 board=self.board, puzzle=self.puzzle_cfg, hover_desk=hover_desk)
        if self.state == "puzzle":
            return layout.render(mood=snap["mood"], snapshot=snap, mode="puzzle",
                                 board=self.board, puzzle=self.puzzle_cfg, hover_cell=hover_cell)
        if self.state == "ending":
            return layout.render(mood=snap["mood"], snapshot=snap, mode="ending", ending=self.verdict)
        page = self.page or self.last_page
        return layout.render(
            mood=snap["mood"], snapshot=snap,
            speaker=page[0], text=page[1],
            options=self.options if self.state == "choice" else (),
            log_lines=self.log, hover_option=hover_option)

    def hit_region(self, lx: float, ly: float) -> str:
        """给外壳做悬停高亮用。顺便把整理台的悬停项记在 self.desk_hover 上。"""
        if self.state == "desk":
            hit = self.desk_hit(lx, ly)
            self.desk_hover = hit if isinstance(hit, tuple) else None
            return "desk" if hit else ""
        if self.state == "choice":
            i = self._hit(self.option_rects(), lx, ly)
            return f"option:{i}" if i is not None else ""
        if self.state == "puzzle":
            i = self._hit(self.cell_rects(), lx, ly)
            if i is not None:
                return f"cell:{i}"
            if self._hit([self.give_up_rect()], lx, ly) is not None:
                return "giveup"
        return ""
