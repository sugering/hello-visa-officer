"""把 dechecker 抠出来的 UI 大图裁好、缩到 demo 实际使用的尺寸，重新打包。

为什么要打包：原始 UI 图是 2752x1536 的整图，元素周围留白极多，6 张就要 21 MB。
demo 只用到其中很小的一块，提前裁好能省掉 90% 体积，画质反而更合适（按显示尺寸 1:1 取样）。

用法： python tools/pack_ui.py
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
UI = ROOT / "assets" / "ui"

# 源图 -> [(裁切框, 输出名, 目标尺寸)]
SRC_CROP = {
    "Game_UI_asset": (204, 436, 2544, 1136),
    "suspicion_meter": (196, 624, 2544, 912),
    "modal_puzzle_frame": (316, 116, 2436, 1440),
    "ui_button_states": (228, 124, 2172, 448),
    "ui_card_states": (96, 456, 780, 1296),
    "verdict_stamps": (28, 120, 600, 412),
}
PLAN = [
    ("Game_UI_asset", (204, 436, 2544, 1136), "dialogue", (1620, 485)),
    ("suspicion_meter", (196, 624, 2544, 912), "meter", (1240, 152)),
    ("modal_puzzle_frame", (316, 116, 2436, 1440), "puzzle", (1400, 875)),
    ("ui_button_states", (228, 124, 2172, 448), "button", (1580, 232)),
    ("ui_card_states", (96, 456, 780, 1296), "card", (342, 432)),
    ("verdict_stamps", (28, 120, 600, 412), "stamp_approved", (920, 620)),
    ("verdict_stamps", (624, 100, 1168, 408), "stamp_denied", (920, 520)),
    ("verdict_stamps", (356, 492, 856, 820), "stamp_review", (920, 600)),
]


def main() -> None:
    total = 0
    for src, box, out_name, size in PLAN:
        path = UI / f"{src}.png"
        if not path.exists():
            print(f"跳过 {out_name}：缺 {path.name}")
            continue
        im = Image.open(path).convert("RGBA").crop(box)
        # 按目标尺寸缩放，保持比例（取较小的缩放比，避免拉伸变形）
        scale = min(size[0] / im.width, size[1] / im.height)
        im = im.resize((max(1, round(im.width * scale)), max(1, round(im.height * scale))), Image.LANCZOS)
        out = UI / f"{out_name}.png"
        im.save(out, optimize=True)
        kb = out.stat().st_size / 1024
        total += kb
        print(f"{out_name:<16} {im.width}x{im.height}  {kb:6.0f} KB")
    print(f"\n合计 {total/1024:.1f} MB -> {UI}")


if __name__ == "__main__":
    main()
