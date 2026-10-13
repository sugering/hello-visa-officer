"""把"透明棋盘格被烧进 JPEG"的 UI 图还原成带 alpha 的 PNG。

背景：AI 出图工具用棋盘格表示透明，导出 JPEG 时棋盘格成了真实像素。
棋盘格是"中性灰 + 规则周期"的人工图案，而 UI 元素（深蓝/米色/红绿图章）都有明显色彩或明度差，
所以可以用"离棋盘两色都很远"来抠出元素。

用法： python tools/dechecker.py [--tol 36] [--erode 1] [--dry]
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "assets" / "ui" / "raw"   # 出图工具导出的原始 JPEG（棋盘格被烧进像素）
DST = ROOT / "assets" / "ui"


def checker_tones(arr: np.ndarray) -> np.ndarray:
    """从四条边框取样，用亮度中位数把棋盘格的两种色调分出来。"""
    h, w, _ = arr.shape
    b = 90
    border = np.concatenate([
        arr[:b, :, :].reshape(-1, 3), arr[-b:, :, :].reshape(-1, 3),
        arr[:, :b, :].reshape(-1, 3), arr[:, -b:, :].reshape(-1, 3),
    ]).astype(np.float32)
    lum = border.mean(axis=1)
    med = np.median(lum)
    light, dark = border[lum >= med], border[lum < med]
    tones = [light.mean(axis=0) if len(light) else med]
    if len(dark) > 100 and abs(dark.mean() - med) > 4:
        tones.append(dark.mean(axis=0))
    return np.stack(tones)


def process(path: Path, tol: float, erode: int, dry: bool) -> dict:
    im = Image.open(path).convert("RGB")
    arr = np.asarray(im).astype(np.float32)
    tones = checker_tones(arr)

    dist = np.min(np.stack([np.abs(arr - t).sum(axis=2) for t in tones]), axis=0)
    bg = Image.fromarray(((dist < tol) * 255).astype(np.uint8), "L")
    bg = bg.filter(ImageFilter.MedianFilter(5))
    for _ in range(erode):
        bg = bg.filter(ImageFilter.MinFilter(3))

    alpha = Image.fromarray((255 - np.asarray(bg)).astype(np.uint8), "L")
    alpha = alpha.filter(ImageFilter.GaussianBlur(0.6))

    out = im.convert("RGBA")
    out.putalpha(alpha)

    stats = {
        "file": path.name,
        "tones": " / ".join("#%02x%02x%02x" % tuple(int(v) for v in t) for t in tones),
        "kept": float((np.asarray(alpha) > 127).mean()),
        "size": f"{im.size[0]}x{im.size[1]}",
    }
    if not dry:
        DST.mkdir(parents=True, exist_ok=True)
        out.save(DST / (path.stem.replace(" ", "_") + ".png"))
    return stats


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tol", type=float, default=36)
    ap.add_argument("--erode", type=int, default=1)
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()

    print(f"{'文件':<28}{'棋盘色调':<22}{'保留像素占比':<14}{'尺寸'}")
    for p in sorted(SRC.glob("*.jpg")):
        s = process(p, args.tol, args.erode, args.dry)
        print(f"{s['file']:<28}{s['tones']:<22}{s['kept']:<14.1%}{s['size']}")
    print(f"\n输出目录: {DST}" + ("（dry run）" if args.dry else ""))


if __name__ == "__main__":
    main()
