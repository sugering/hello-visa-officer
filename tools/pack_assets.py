"""把美术素材压到 demo 实际需要的分辨率，减小仓库体积。

仓库里放压缩版；全分辨率母版留在本机的 Officer/ backgrounds/ items/ ui/ 四个目录里（已被 .gitignore 排除）。
用法： python tools/pack_assets.py [--dry]
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
JOBS = [
    ("assets/characters/officer", 1920, 88),
    ("assets/backgrounds", 1920, 88),
    ("assets/items", 1600, 85),
]


def main() -> None:
    dry = "--dry" in sys.argv
    before = after = 0
    for rel, max_w, quality in JOBS:
        for p in sorted((ROOT / rel).glob("*.jpg")):
            size_before = p.stat().st_size
            im = Image.open(p).convert("RGB")
            if im.width > max_w:
                im = im.resize((max_w, round(im.height * max_w / im.width)), Image.LANCZOS)
            if not dry:
                im.save(p, quality=quality, optimize=True, progressive=True)
            size_after = p.stat().st_size if not dry else size_before
            before += size_before
            after += size_after
            print(f"{p.name:<32} {im.width:>5}x{im.height:<5} {size_before/1024:7.0f} -> {size_after/1024:7.0f} KB")
    print(f"\n合计 {before/1024/1024:.1f} MB -> {after/1024/1024:.1f} MB" + ("（dry run）" if dry else ""))


if __name__ == "__main__":
    main()
