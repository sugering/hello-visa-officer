"""离线出预览图：把 demo 的三种画面渲染成 PNG。

没有显示器也能验证版面 —— 先出图、肉眼看，再改 layout.py。
运行： python demo/preview.py
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from session import Session        # noqa: E402

OUT = HERE / "preview"
OUT.mkdir(exist_ok=True)


def to_choice(s: Session, solve: bool = True) -> None:
    guard = 0
    while s.state in ("line", "puzzle", "desk") and guard < 300:
        guard += 1
        if s.state == "line":
            s.advance()
        elif solve:
            s.solve_puzzle()
        else:
            s.finish_puzzle(False, 0)


def to_interlude(s: Session) -> None:
    """走到"流水被击穿 → 打开整理台"那一刻。"""
    while s.state == "line":
        s.advance()


def advance_to_repair(s: Session) -> None:
    """走到「流水被击穿 → 弹窗修补」那一刻。"""
    for pick in ("把护照和邀请函推过去", "参加行业会议", "这是我多年的积蓄"):
        to_choice(s, solve=True)
        s.choose_by_text(pick)
    to_interlude(s)


def main() -> None:
    # ① 对局中：修补完成后回到面试，材料面板能看到「已击穿」与新增的整理版流水
    s = Session()
    advance_to_repair(s)
    s.solve_puzzle(policy="balanced")
    to_choice(s, solve=True)
    s.frame(hover_option=0).convert("RGB").save(OUT / "01_interview.jpg", quality=88)

    # ② 文件整理室：把被击穿的流水重做一遍（保守 / 动手脚，逐行选）
    s2 = Session()
    advance_to_repair(s2)
    s2.board.auto("balanced")
    s2.frame(hover_desk=("amount", "bold")).convert("RGB").save(OUT / "02_desk.jpg", quality=88)

    # ③ 结局
    s3 = Session()
    for pick in ("把护照和邀请函推过去", "参加行业会议", "这是我多年的积蓄",
                 "重新整理", "做工程师", "坐直"):
        to_choice(s3, solve=True)
        s3.choose_by_text(pick)
    to_choice(s3, solve=True)
    s3.frame().convert("RGB").save(OUT / "03_ending.jpg", quality=88)

    for p in sorted(OUT.glob("*.jpg")):
        print("已出图:", p.relative_to(HERE.parent))


if __name__ == "__main__":
    main()
