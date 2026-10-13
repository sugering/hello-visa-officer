"""核心循环回归测试：把设计里的规则钉成可执行断言。

运行： python -m unittest -v test_engine
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from engine import Interview, OptionLocked   # noqa: E402
from puzzles import make_puzzle              # noqa: E402


def solve_puzzle(eng, ev, policy="balanced"):
    """统一处理两类谜题：翻转棋盘用标准解，整理流水用指定的取舍策略。"""
    board = make_puzzle(ev["config"]["type"], ev["config"])
    payload = None
    if hasattr(board, "auto"):
        board.auto(policy)
        payload = board.outcome()
    else:
        board.apply(board.solve())
    return eng.apply_puzzle_result(ev["id"], board.is_solved(), board.move_count, payload)


def play(route, policy="balanced"):
    eng = Interview.from_files()
    for option_id in route:
        if eng.ended:
            break
        events = eng.choose(option_id)
        for ev in events:
            if ev["type"] == "puzzle":
                solve_puzzle(eng, ev, policy)
    return eng


GOOD = ["hand_over", "state_conference", "cite_bank", "resubmit_clean", "cite_job", "wait_result"]
BLUFF = ["hand_over", "state_tourism", "cite_company", "joke", "wait_result"]
BARE = ["wait_silent", "state_tourism", "vague", "joke", "wait_result"]


class PuzzleTest(unittest.TestCase):
    def test_lights_out_has_solution_and_it_solves(self):
        board = make_puzzle("lights_out", {"size": 3, "initial": [1, 0, 0, 0, 1, 1, 0, 0, 1]})
        solution = board.solve()
        self.assertIsNotNone(solution)
        board.apply(solution)
        self.assertTrue(board.is_solved())
        self.assertEqual(board.move_count, 3)

    def test_puzzle_reward_within_budget(self):
        eng = Interview.from_files()
        events = eng.apply_puzzle_result("seal_align", True, 3)
        self.assertIn("bank_statement_clean", eng.owned)
        self.assertNotIn("存款日期集中", eng.sheet["bank_statement"].flaws)
        self.assertIn("seal_solved", eng.flags)
        self.assertEqual(eng.suspicion, 0)   # 5 - 5
        self.assertTrue(any(e["type"] == "material_improved" for e in events))

    def test_puzzle_failure_costs_suspicion(self):
        eng = Interview.from_files()
        eng.apply_puzzle_result("seal_align", False, 0)
        self.assertEqual(eng.suspicion, 17)  # 5 + 12
        self.assertNotIn("bank_statement_clean", eng.owned)


class PatchStatementTest(unittest.TestCase):
    """整理流水：可信度与破绽的取舍，以及"账目必须自洽"的耦合规则。"""

    def board(self):
        cfg = Interview.from_files().puzzle_defs["patch_statement"]
        return make_puzzle(cfg["type"], cfg)

    def test_safe_and_bold_are_a_real_tradeoff(self):
        b = self.board()
        b.auto("safe")
        self.assertEqual(b.flaws(), [])
        self.assertEqual(b.robustness(), 80)
        safe_cred = b.credibility()

        b.auto("bold")
        self.assertEqual(len(b.flaws()), 5)
        self.assertEqual(b.robustness(), 30)           # 扣到下限，比原始伪造流水还脆
        self.assertGreater(b.credibility(), safe_cred)
        self.assertEqual(b.credibility(), 92)          # 撞到上限：好看是有的，代价在抗性上

    def test_coupling_adds_a_flaw_when_books_dont_balance(self):
        b = self.board()
        b.auto("safe")
        b.pick("amount", "bold")                      # 金额动了，余额没动
        self.assertIn("总账对不上", b.flaws())
        b.pick("balance", "bold")                     # 两边一起动，账就平了
        self.assertNotIn("总账对不上", b.flaws())

    def test_incomplete_patch_is_not_solved(self):
        b = self.board()
        b.pick("header", "bold")
        self.assertFalse(b.is_solved())

    def test_payload_is_written_into_the_granted_material(self):
        eng = Interview.from_files()
        b = self.board()
        b.auto("bold")
        eng.apply_puzzle_result("patch_statement", True, b.moves, b.outcome())
        m = eng.sheet["bank_statement_clean"]
        self.assertEqual(m.credibility, 92)
        self.assertEqual(m.robustness, 30)
        self.assertEqual(len(m.flaws), 5)
        self.assertIn("patched_statement", eng.flags)

    def test_balanced_policy_keeps_the_books_straight(self):
        b = self.board()
        b.auto("balanced")
        self.assertTrue(b.is_solved())
        self.assertNotIn("总账对不上", b.flaws())
        self.assertEqual(len(b.flaws()), 2)


class GatingTest(unittest.TestCase):
    def test_option_requires_material(self):
        eng = Interview.from_files()
        eng.choose("hand_over")
        eng.choose("state_conference")
        eng.choose("cite_bank")            # 流水被击穿 → 进入修补节点
        options = {o["option"].id: o for o in eng.available_options()}
        self.assertTrue(options["resubmit_clean"]["locked"])   # 没解谜就拿不到整理版流水
        with self.assertRaises(OptionLocked):
            eng.choose("resubmit_clean")

    def test_conflict_preview_warns_before_choosing(self):
        eng = Interview.from_files()
        eng.choose("hand_over")
        opt = next(o for o in eng.node.options if o.id == "state_tourism")
        preview = eng.preview_conflicts(opt)
        self.assertEqual(preview[0]["with"], "purpose:conference")


class ConsistencyTest(unittest.TestCase):
    def test_statement_contradicting_material_is_caught(self):
        eng = Interview.from_files()
        eng.choose("hand_over")
        before = eng.suspicion
        eng.choose("state_tourism")         # 材料写会议，嘴上说旅游
        self.assertIn("caught_lying", eng.flags)
        self.assertGreaterEqual(eng.suspicion - before, 25)
        self.assertEqual(eng.mood, "caught")

    def test_forged_material_collapses_under_probe(self):
        eng = Interview.from_files()
        eng.choose("hand_over")
        eng.choose("state_conference")
        eng.choose("cite_bank")
        self.assertIn("broke:bank_statement", eng.flags)
        self.assertIn("bank_statement", eng.exposed)
        self.assertGreaterEqual(eng.suspicion, 20)

    def test_genuine_material_holds(self):
        eng = Interview.from_files()
        eng.choose("hand_over")
        eng.choose("state_conference")      # 邀请函 抗性70 > 压力30
        self.assertNotIn("broke:invitation", eng.flags)


class VerdictTest(unittest.TestCase):
    def test_good_route_is_approved(self):
        eng = play(GOOD)
        self.assertEqual(eng.ended, "approved")
        self.assertGreater(eng.verdict["score"], 100)
        self.assertEqual(eng.verdict["missing"], [])

    def test_bluff_route_gets_reviewed_or_worse(self):
        eng = play(BLUFF)
        self.assertIn(eng.ended, ("administrative_review", "denied"))
        self.assertTrue(eng.verdict["caught_lying"])
        self.assertIn("funds", eng.verdict["missing"])

    def test_empty_hands_is_denied(self):
        eng = play(BARE)
        self.assertEqual(eng.ended, "denied")

    def test_round_limit_forces_a_verdict(self):
        eng = Interview.from_files()
        eng.choose("hand_over")
        eng.choose("state_conference")
        eng.choose("cite_company")
        eng.choose("joke")
        eng.round = eng.scenario["round_limit"]
        eng.choose("wait_result")
        self.assertEqual(eng.verdict["reason"], "round_limit")
        self.assertIsNotNone(eng.ended)


class PresentationTest(unittest.TestCase):
    def test_mood_bands_map_to_five_expressions(self):
        eng = Interview.from_files()
        for suspicion, mood in ((0, "calm"), (25, "doubt"), (50, "impatient"), (90, "caught")):
            eng.suspicion = suspicion
            eng.forced_mood = None
            self.assertEqual(eng.mood, mood)

    def test_intrigue_overrides_band(self):
        eng = Interview.from_files()
        eng.choose("wait_silent")
        eng.choose("name_drop")             # 抛出"硅谷投资人" → 突然感兴趣
        self.assertEqual(eng.mood, "interested")


if __name__ == "__main__":
    unittest.main(verbosity=2)
