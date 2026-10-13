"""谜题层：与对话循环完全解耦的纯状态机。

设计约束
--------
* 只依赖标准库，不 import renpy / pygame —— 谜题既能跑在终端原型里，
  也能原样搬进 Ren'Py 的 screen + python 块。
* 谜题的输入是 **操作序列**，输出是 (是否完成, 消耗步数)。
  这样表现层负责"手感"，引擎只负责"结果"，方便离线跑回归测试。
* 每个谜题都要能给出标准解（solve()），用于自动化测试与"提示"功能。

当前实现：LightsOut（印章/光线对齐：点一格翻转自己与上下左右）
—— 玩法上等价于"调整盖章位置/光圈对齐"，代码上可穷举出最短解。
"""

from __future__ import annotations

from itertools import combinations
from typing import Iterable, List, Optional


class LightsOut:
    """size x size 的翻转棋盘。点 (r, c) 会翻转自身与上下左右四格。"""

    def __init__(self, size: int = 3, initial: Optional[Iterable[int]] = None) -> None:
        self.size = size
        self.cells = list(initial) if initial is not None else [0] * (size * size)
        if len(self.cells) != size * size:
            raise ValueError("initial 长度必须等于 size*size")
        self.cells = [1 if v else 0 for v in self.cells]
        self.moves: List[int] = []

    # ---- 基本操作 ----------------------------------------------------
    def neighbors(self, index: int) -> List[int]:
        r, c = divmod(index, self.size)
        out = [index]
        if r > 0:
            out.append(index - self.size)
        if r < self.size - 1:
            out.append(index + self.size)
        if c > 0:
            out.append(index - 1)
        if c < self.size - 1:
            out.append(index + 1)
        return out

    def toggle(self, index: int) -> None:
        for i in self.neighbors(index):
            self.cells[i] ^= 1
        self.moves.append(index)

    def apply(self, sequence: Iterable[int]) -> None:
        for index in sequence:
            self.toggle(index)

    def is_solved(self) -> bool:
        return all(cell == 0 for cell in self.cells)

    @property
    def move_count(self) -> int:
        return len(self.moves)

    # ---- 求解 --------------------------------------------------------
    def solve(self, max_moves: Optional[int] = None) -> Optional[List[int]]:
        """穷举最短解。翻转子集可交换，所以只需枚举组合；3x3 时最多 512 种。"""
        limit = self.size * self.size if max_moves is None else min(max_moves, self.size * self.size)
        for k in range(limit + 1):
            for combo in combinations(range(self.size * self.size), k):
                probe = LightsOut(self.size, self.cells)
                probe.apply(combo)
                if probe.is_solved():
                    return list(combo)
        return None

    def render(self) -> str:
        """终端渲染：■ 表示待处理的错位，· 表示已对齐。"""
        rows = []
        for r in range(self.size):
            rows.append(" ".join("■" if self.cells[r * self.size + c] else "·"
                                 for c in range(self.size)))
        return "\n".join(rows)


class PatchStatement:
    """整理流水：对着单子逐项做取舍，把一张旧流水"修"成能递出去的样子。

    每一行（槽位）有两个选项：
      * safe —— 照原样保留，可信度低但**不留破绽**
      * bold —— 动过手脚，可信度高但**引入破绽**

    破绽数直接扣抗性，而抗性决定它在面试里会不会被追问击穿。
    于是玩家真正的选择不是"改不改"，而是"我愿意为这几个分数承担几次被看穿的风险"。

    还有一个耦合规则：某些槽位必须同进同退（比如"金额"和"余额"一个动了一个没动，
    账就不平了），多出来的破绽会写进材料，成为面试里的把柄。
    """

    kind = "patch_statement"

    def __init__(self, cfg: dict) -> None:
        self.slots = cfg["slots"]
        self.base_credibility = cfg.get("base_credibility", 20)
        self.cap_credibility = cfg.get("cap_credibility", 92)
        self.base_robustness = cfg.get("base_robustness", 80)
        self.per_flaw = cfg.get("robustness_per_flaw", -12)
        self.min_robustness = cfg.get("min_robustness", 30)
        self.couplings = cfg.get("coupling", [])
        self.picks = {}          # slot_id -> "safe" | "bold"
        self.moves = 0           # 玩家改动次数
        self.size = len(self.slots)

    # ---- 操作 --------------------------------------------------------
    def pick(self, slot_id: str, which: str) -> bool:
        if slot_id not in {s["id"] for s in self.slots} or which not in ("safe", "bold"):
            return False
        if self.picks.get(slot_id) == which:
            return False
        self.picks[slot_id] = which
        self.moves += 1
        return True

    def clear(self, slot_id: str) -> bool:
        if slot_id in self.picks:
            del self.picks[slot_id]
            self.moves += 1
            return True
        return False

    def reset(self) -> None:
        self.picks.clear()
        self.moves = 0

    @property
    def filled(self) -> int:
        return len(self.picks)

    @property
    def move_count(self) -> int:
        """和 LightsOut 保持同一套接口，引擎与表现层不必区分谜题类型。"""
        return self.moves

    def is_solved(self) -> bool:
        return self.filled == len(self.slots)

    def choice_of(self, slot: dict):
        which = self.picks.get(slot["id"])
        return slot.get(which) if which else None

    # ---- 结算 --------------------------------------------------------
    def flaws(self) -> list:
        out = []
        for slot in self.slots:
            c = self.choice_of(slot)
            if c and c.get("flaw"):
                out.append(c["flaw"])
        for rule in self.couplings:
            a, b = rule["slots"]
            if rule.get("rule", "differ") == "differ" and self.picks.get(a) != self.picks.get(b):
                out.append(rule["flaw"])
        return out

    def credibility(self) -> int:
        total = self.base_credibility + sum(
            (self.choice_of(s) or {}).get("credibility", 0) for s in self.slots)
        return min(self.cap_credibility, total)

    def robustness(self) -> int:
        return max(self.min_robustness, self.base_robustness + self.per_flaw * len(self.flaws()))

    def outcome(self) -> dict:
        return {"credibility": self.credibility(), "robustness": self.robustness(),
                "flaws": self.flaws(), "moves": self.moves}

    # ---- 给测试与"提示"用的自动打法 ----------------------------------
    def auto(self, policy: str = "balanced") -> None:
        """safe=全保守；bold=全激进；balanced=能占便宜的地方动手，但守住账目平衡。"""
        self.reset()
        for slot in self.slots:
            if policy == "safe":
                self.pick(slot["id"], "safe")
            elif policy == "bold":
                self.pick(slot["id"], "bold")
            else:
                self.pick(slot["id"], "bold" if slot.get("balanced_bold") else "safe")

    def render(self) -> str:
        rows = []
        for s in self.slots:
            mark = {"safe": "◇", "bold": "◆", None: "·"}[self.picks.get(s["id"])]
            rows.append(f"{mark} {s['label']}")
        return "\n".join(rows)


def make_puzzle(kind: str, cfg: dict):
    """按 puzzles.json 的配置实例化谜题。"""
    if kind == "lights_out":
        return LightsOut(size=cfg.get("size", 3), initial=cfg.get("initial"))
    if kind == "patch_statement":
        return PatchStatement(cfg)
    raise ValueError(f"未知谜题类型: {kind}")
