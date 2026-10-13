"""端到端流程回归 —— 不建窗口、不需要显示器，直接驱动 Session 打通关。

这就是"逻辑测试"的核心：把玩家会做的点击（用真实逻辑坐标算出来）喂进去，
断言结局、怀疑度、材料状态。人工玩一遍会漏的东西，这里跑一遍就抓住了。

运行： python demo/test_flow.py
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from session import Session        # noqa: E402


def click_rect(session: Session, rect) -> None:
    x, y, w, h = rect
    session.on_click(x + w / 2, y + h / 2)


def to_choice(session: Session, solve: bool = True) -> None:
    """推演到等待玩家选择的界面（台词自动翻页，解谜按参数处理）。"""
    guard = 0
    while session.state in ("line", "puzzle", "desk") and guard < 300:
        guard += 1
        if session.state == "line":
            session.advance()
        elif solve:
            session.solve_puzzle()
        else:
            session.finish_puzzle(False, 0)
    if guard >= 300:
        raise AssertionError("状态机卡住了")


def play(picks, solve: bool = True) -> Session:
    """按顺序选话术打通一局，返回结束时的 Session。"""
    s = Session()
    for pick in picks:
        to_choice(s, solve)
        if s.state != "choice":
            break
        if not s.choose_by_text(pick):
            raise AssertionError(
                f"选不到「{pick}」；当前选项：" + str([o["option"].text for o in s.options]))
    to_choice(s, solve)
    return s


GOOD = ["把护照和邀请函推过去", "参加行业会议", "这是我多年的积蓄",
        "重新整理", "做工程师", "坐直"]
BARE = ["不出声", "跟团旅游", "钱不是问题", "我妈做的菜", "坐直"]
BLUFF = ["把护照和邀请函推过去", "跟团旅游", "公司全额报销", "我妈做的菜", "坐直"]


class FlowTest(unittest.TestCase):
    def test_good_route_is_approved(self):
        s = play(GOOD)
        self.assertEqual(s.state, "ending")
        self.assertEqual(s.eng.ended, "approved")
        self.assertGreater(s.eng.verdict["score"], 100)
        self.assertFalse(s.eng.verdict["caught_lying"])

    def test_good_route_survives_one_break(self):
        """核心体验：伪造流水被击穿一次，靠解谜修补后仍然通关。"""
        s = play(GOOD)
        self.assertIn("broke:bank_statement", s.eng.flags)
        self.assertIn("bank_statement", s.eng.exposed)
        self.assertTrue(any("获得《重新整理的银行流水》" in l for l in s.log))
        self.assertTrue(any("整理完成《重新整理的银行流水》" in l for l in s.log))

    def test_bare_route_is_denied(self):
        s = play(BARE)
        self.assertEqual(s.eng.ended, "denied")

    def test_bluff_route_is_caught_lying(self):
        s = play(BLUFF)
        self.assertTrue(s.eng.verdict["caught_lying"])
        self.assertIn(s.eng.ended, ("denied", "administrative_review", "caught"))

    def test_locked_option_does_not_advance(self):
        s = Session()
        to_choice(s, solve=False)          # 第一次到选择：开场
        s.choose_by_text("把护照和邀请函推过去")
        to_choice(s, solve=False)
        s.choose_by_text("参加行业会议")
        to_choice(s, solve=False)
        s.choose_by_text("这是我多年的积蓄")   # 流水被击穿 → 进修补节点（不解谜）
        to_choice(s, solve=False)
        self.assertEqual(s.state, "choice")
        locked = [o for o in s.options if o["locked"]]
        self.assertTrue(locked, "应该有一个因为缺材料而锁住的选项")
        before = s.eng.round
        self.assertFalse(s.choose_by_text("重新整理"))
        self.assertEqual(s.eng.round, before, "锁住的选项不该消耗回合")

    def test_click_on_locked_option_is_ignored(self):
        s = Session()
        to_choice(s, solve=False)
        s.choose_by_text("把护照和邀请函推过去")
        to_choice(s, solve=False)
        s.choose_by_text("参加行业会议")
        to_choice(s, solve=False)
        s.choose_by_text("这是我多年的积蓄")
        to_choice(s, solve=False)
        idx = next(i for i, o in enumerate(s.options) if o["locked"])
        click_rect(s, s.option_rects()[idx])
        self.assertEqual(s.state, "choice")
        self.assertTrue(any("不可选" in l for l in s.log), "点击被锁选项应给出提示日志")

    def _to_desk(self) -> Session:
        """走到「流水被击穿 → 整理台」那一刻。"""
        s = Session()
        for pick in ("把护照和邀请函推过去", "参加行业会议", "这是我多年的积蓄"):
            to_choice(s, solve=True)
            s.choose_by_text(pick)
        while s.state == "line":
            s.advance()
        return s

    def test_repair_node_opens_the_desk(self):
        s = self._to_desk()
        self.assertEqual(s.state, "desk", "修补节点应该打开文件整理台，而不是抽象弹窗")
        self.assertEqual(len(s.board.slots), 5)

    def test_desk_is_a_real_tradeoff(self):
        """全保守 → 干净但分低；全激进 → 好看但脆。玩家在两条线之间选。"""
        s = self._to_desk()
        for i in range(5):
            click_rect(s, s.desk_choice_rect(i, "safe"))
        self.assertEqual((s.board.credibility(), s.board.robustness(), len(s.board.flaws())), (71, 80, 0))

        for i in range(5):
            click_rect(s, s.desk_choice_rect(i, "bold"))
        self.assertEqual((s.board.credibility(), s.board.robustness(), len(s.board.flaws())), (92, 30, 5))

    def test_clicking_through_the_desk_grants_the_material(self):
        s = self._to_desk()
        for i in range(5):
            click_rect(s, s.desk_choice_rect(i, "bold"))
        click_rect(s, s.desk_submit_rect())
        self.assertIn("bank_statement_clean", s.eng.owned)
        m = s.eng.sheet["bank_statement_clean"]
        self.assertEqual((m.credibility, m.robustness, len(m.flaws)), (92, 30, 5))
        self.assertIn("patched_statement", s.eng.flags)

    def test_submitting_an_unfinished_sheet_is_refused(self):
        s = self._to_desk()
        click_rect(s, s.desk_choice_rect(0, "safe"))
        click_rect(s, s.desk_submit_rect())
        self.assertEqual(s.state, "desk")
        self.assertTrue(any("先做决定" in l for l in s.log))
        self.assertNotIn("bank_statement_clean", s.eng.owned)

    def test_declining_the_repair_keeps_the_old_path_open(self):
        """不整理原样交上去 → 拿不到整理版流水，但还能硬扛（hold_line）。"""
        s = self._to_desk()
        before = s.eng.suspicion
        click_rect(s, s.desk_skip_rect())
        self.assertNotIn("bank_statement_clean", s.eng.owned)
        self.assertGreater(s.eng.suspicion, before)
        self.assertEqual(s.state, "choice")

    def test_puzzle_state_is_not_reachable_from_the_repair_node(self):
        s = self._to_desk()
        self.assertNotEqual(s.state, "puzzle")

    def test_hover_region_reports_option_and_cell(self):
        s = Session()
        to_choice(s, solve=True)
        x, y, w, h = s.option_rects()[0]
        self.assertEqual(s.hit_region(x + w / 2, y + h / 2), "option:0")
        self.assertEqual(s.hit_region(10, 10), "")

    def test_advancing_through_lines_never_loops_forever(self):
        s = Session()
        to_choice(s, solve=True)
        self.assertIn(s.state, ("choice", "ending"))


if __name__ == "__main__":
    unittest.main(verbosity=2)