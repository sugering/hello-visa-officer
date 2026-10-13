"""《你好签证官》逻辑测试 Demo —— tkinter 外壳（很薄）。

零安装：只用 Python 自带的 tkinter + Pillow，不需要 Ren'Py / pygame。
玩法状态全在 demo/session.py，画面全在 demo/layout.py；这里只负责窗口、缩放、鼠标坐标。

运行：
    python demo/app.py             # 开始玩
    python demo/app.py --selftest  # 建窗口 → 截图 → 退出（无需人工干预）
按键：空格/回车 = 继续　R = 重开　S = 截图　Esc = 退出
"""

from __future__ import annotations

import sys
import tkinter as tk
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from PIL import Image, ImageTk                    # noqa: E402

from session import Session                       # noqa: E402
from theme import SCREEN                          # noqa: E402


class DemoApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.canvas = tk.Canvas(root, width=SCREEN[0], height=SCREEN[1],
                                highlightthickness=0, bg="#0b0c10")
        self.canvas.pack(fill="both", expand=True)
        self._photo = None
        self._frame = None
        self.scale = 1.0
        self.offset = (0.0, 0.0)
        self.hover = ""
        self.shots = 0
        self.session = Session()
        self.hover_option = None
        self.hover_cell = None

        root.bind("<Button-1>", self.on_click)
        root.bind("<Motion>", self.on_motion)
        root.bind("<Key-space>", lambda e: self.advance())
        root.bind("<Return>", lambda e: self.advance())
        root.bind("<Key-r>", lambda e: self.restart())
        root.bind("<Key-s>", lambda e: self.screenshot())
        root.bind("<Escape>", lambda e: root.destroy())
        root.bind("<Configure>", lambda e: self.render())

    # ---- 输入 --------------------------------------------------------
    def to_logical(self, x: int, y: int):
        return ((x - self.offset[0]) / self.scale, (y - self.offset[1]) / self.scale)

    def advance(self) -> None:
        self.session.advance()
        self.render()

    def restart(self) -> None:
        self.session.reset()
        self.hover_option = self.hover_cell = None
        self.render()

    def on_click(self, event) -> None:
        lx, ly = self.to_logical(event.x, event.y)
        self.session.on_click(lx, ly)
        self.render()

    def on_motion(self, event) -> None:
        lx, ly = self.to_logical(event.x, event.y)
        region = self.session.hit_region(lx, ly)
        if region != self.hover:
            self.hover = region
            self.hover_option = int(region.split(":")[1]) if region.startswith("option:") else None
            self.hover_cell = int(region.split(":")[1]) if region.startswith("cell:") else None
            self.render()

    # ---- 渲染 --------------------------------------------------------
    def render(self) -> None:
        img = self.session.frame(hover_option=self.hover_option, hover_cell=self.hover_cell,
                                 hover_desk=self.session.desk_hover)
        self._frame = img
        w, h = self.canvas.winfo_width(), self.canvas.winfo_height()
        if w < 10 or h < 10:
            w, h = SCREEN
        self.scale = min(w / SCREEN[0], h / SCREEN[1])
        tw, th = max(1, int(SCREEN[0] * self.scale)), max(1, int(SCREEN[1] * self.scale))
        self.offset = ((w - tw) / 2, (h - th) / 2)
        self._photo = ImageTk.PhotoImage(img.resize((tw, th), Image.LANCZOS))
        self.canvas.delete("all")
        self.canvas.create_image(self.offset[0], self.offset[1], anchor="nw", image=self._photo)

    def screenshot(self) -> None:
        self.shots += 1
        out = HERE / "preview" / f"shot_{self.shots:02d}.jpg"
        out.parent.mkdir(exist_ok=True)
        (self._frame or self.session.frame()).convert("RGB").save(out, quality=88)
        print("截图:", out)


def main() -> None:
    selftest = "--selftest" in sys.argv
    root = tk.Tk()
    root.title("你好签证官 · 逻辑测试 Demo")
    root.geometry("1600x900")
    app = DemoApp(root)
    if selftest:
        root.update_idletasks()
        root.update()
        app.render()
        app.screenshot()
        root.destroy()
        return
    root.mainloop()


if __name__ == "__main__":
    main()
