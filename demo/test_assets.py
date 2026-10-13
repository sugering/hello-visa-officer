"""资产与引擎的一致性测试：任何一处命名对不上，这里立刻红。

这就是"逻辑测试 demo"的自动化部分 —— 手工玩一遍容易漏掉 officer_clam 这种拼写错误，机器不会。
运行： python demo/test_assets.py
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "prototype"))

import theme                                        # noqa: E402
from engine import Interview                        # noqa: E402


class AssetTest(unittest.TestCase):
    def setUp(self):
        self.eng = Interview.from_files()

    def test_every_mood_has_an_image(self):
        for mood, rel in theme.MOOD_FILE.items():
            with self.subTest(mood=mood):
                self.assertTrue((theme.ASSETS / rel).exists(), f"{mood} 缺图: {rel}")

    def test_engine_moods_are_covered(self):
        # 引擎可能返回的表情集合必须都有立绘，否则运行时会 KeyError
        for mood in ("calm", "doubt", "impatient", "interested", "caught"):
            self.assertIn(mood, theme.MOOD_FILE)

    def test_every_material_has_an_item_image(self):
        for mid in self.eng.material_defs:
            with self.subTest(material=mid):
                self.assertTrue((theme.ASSETS / f"items/item_{mid}.jpg").exists(),
                                f"材料 {mid} 缺道具图")

    def test_every_background_exists(self):
        for name in ("room_interview", "room_docs", "hall_embassy"):
            self.assertTrue((theme.ASSETS / f"backgrounds/{name}.jpg").exists())

    def test_ui_assets_are_packed_and_sane(self):
        """UI 元素由 tools/pack_ui.py 打包；这里保证它们存在、有透明通道、尺寸够用。"""
        for key, rel in theme.UI_FILE.items():
            with self.subTest(ui=key):
                path = theme.ASSETS / rel
                self.assertTrue(path.exists(), f"缺 UI 图 {rel}")
                im = theme.load(rel)
                self.assertGreaterEqual(im.width, 300, f"{key} 宽度太小，放大后会糊")
                self.assertEqual(im.mode, "RGBA", f"{key} 没有透明通道")

    def test_ui_assets_are_not_oversized(self):
        """防止有人把 20 MB 的整图又塞回仓库。"""
        total = sum((theme.ASSETS / rel).stat().st_size for rel in set(theme.UI_FILE.values()))
        self.assertLess(total, 8 * 1024 * 1024, f"UI 图共 {total/1024/1024:.1f} MB，应该跑一遍 tools/pack_ui.py")

    def test_puzzle_configs_are_implemented(self):
        from puzzles import make_puzzle
        for pid, cfg in self.eng.puzzle_defs.items():
            with self.subTest(puzzle=pid):
                board = make_puzzle(cfg["type"], cfg)
                if hasattr(board, "solve"):
                    self.assertIsNotNone(board.solve(), f"{pid} 无解")
                else:
                    board.auto("balanced")          # 整理类谜题：验证默认策略能走完
                    self.assertTrue(board.is_solved(), f"{pid} 的配置走不完")

    def test_dialogue_goto_targets_exist(self):
        for nid, node in self.eng.node_defs.items():
            for opt in node.options:
                targets = opt.goto.values() if isinstance(opt.goto, dict) else [opt.goto]
                for t in targets:
                    if t is None:
                        continue
                    with self.subTest(node=nid, option=opt.id):
                        self.assertIn(t, self.eng.node_defs, f"{nid}:{opt.id} 指向不存在的节点 {t}")

    def test_option_text_and_ids_are_unique_and_nonempty(self):
        for nid, node in self.eng.node_defs.items():
            ids = [o.id for o in node.options]
            self.assertEqual(len(ids), len(set(ids)), f"{nid} 有重复选项 id")
            for opt in node.options:
                self.assertTrue(opt.text.strip(), f"{nid}:{opt.id} 文本为空")


if __name__ == "__main__":
    unittest.main(verbosity=2)
