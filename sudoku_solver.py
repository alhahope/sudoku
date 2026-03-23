#!/usr/bin/env python3
"""
Sudoku Solver — Native Python GUI (Canvas button version)
运行: conda activate sudoku && python sudoku_solver.py
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import threading


# ─────────────────────────────────────────────────────────────────────────────
# 求解器（MRV 回溯，候选数预计算）
# ─────────────────────────────────────────────────────────────────────────────

def solve(board):
    """
    MRV（最少剩余候选数）回溯求解，board 原地修改。
    速度比朴素回溯快数倍，尤其在困难数独上优势明显。
    """
    flat = [board[r][c] for r in range(9) for c in range(9)]
    _mrvsolve(flat)
    for i, v in enumerate(flat):
        board[i // 9][i % 9] = v


def _mrvsolve(flat):
    """对 flat（81 元素列表）求解，返回是否找到解"""
    # ── 计算所有空格的候选数 ──
    candidates = {}
    for i in range(81):
        if flat[i] == 0:
            avail = set(range(1, 10))
            r, c = i // 9, i % 9
            # 排除同行（row r 的 9 个格子）
            for k in range(r * 9, r * 9 + 9):
                avail.discard(flat[k])
            # 排除同列（col c 的 9 个格子）
            for k in range(c, 81, 9):
                avail.discard(flat[k])
            # 排除同宫
            br, bc = (r // 3) * 3, (c // 3) * 3
            for rr in range(br, br + 3):
                for cc in range(bc, bc + 3):
                    avail.discard(flat[rr * 9 + cc])
            candidates[i] = list(avail)

    # ── MRV：选候选数最少的空格优先填 ──
    if not candidates:
        return True    # 所有空格填满，解已找到

    idx = min(candidates, key=lambda i: len(candidates[i]))
    for v in candidates[idx]:
        flat[idx] = v
        if _mrvsolve(flat):
            return True
        flat[idx] = 0   # 回溯

    return False


def _is_valid(board, row, col, num):
    if num in board[row]:
        return False
    for r in range(9):
        if board[r][col] == num:
            return False
    br, bc = (row // 3) * 3, (col // 3) * 3
    for r in range(br, br + 3):
        for c in range(bc, bc + 3):
            if board[r][c] == num:
                return False
    return True


def check_errors(board):
    errors = []
    for r in range(9):
        for c in range(9):
            if board[r][c] == 0:
                continue
            saved = board[r][c]
            board[r][c] = 0
            if not _is_valid(board, r, c, saved):
                errors.append((r, c))
            board[r][c] = saved
    return errors


def count_filled(board):
    return sum(1 for r in board for v in r if v != 0)


# ─────────────────────────────────────────────────────────────────────────────
# 自定义按钮（Canvas 绘制，绕过 macOS 按钮渲染）
# ─────────────────────────────────────────────────────────────────────────────

class FlatButton(tk.Canvas):
    """扁平化按钮，背景色固定，不会被 macOS 焦点样式影响"""

    def __init__(self, parent, text, bg, fg, command, width=80, height=44, font_size=13):
        bw = width
        bh = height
        self._bg = bg
        self._fg = fg
        self._text = text
        self._command = command
        self._hover = False
        self._pressed = False
        self._bw = bw
        self._bh = bh
        super().__init__(
            parent, width=bw, height=bh,
            bg=bg, highlightthickness=0, bd=0,
            cursor="hand2",
        )

        self.create_text(
            bw // 2, bh // 2,
            text=text,
            fill=fg,
            font=("Arial", font_size, "bold"),
            anchor="center",
        )
        self.create_round_rect(4, 4, bw - 4, bh - 4, radius=8, fill=bg, outline=bg)

        self.bind("<Button-1>", self._down)
        self.bind("<ButtonRelease-1>", self._up)
        self.bind("<Enter>", lambda _: self._set_hover(True))
        self.bind("<Leave>", lambda _: self._set_hover(False))

    def create_round_rect(self, x1, y1, x2, y2, radius, fill, outline):
        """画圆角矩形"""
        r = radius
        self.create_arc(x1, y1, x1 + 2*r, y1 + 2*r, start=90, extent=90, fill=fill, outline="")
        self.create_arc(x2 - 2*r, y1, x2, y1 + 2*r, start=0, extent=90, fill=fill, outline="")
        self.create_arc(x1, y2 - 2*r, x1 + 2*r, y2, start=180, extent=90, fill=fill, outline="")
        self.create_arc(x2 - 2*r, y2 - 2*r, x2, y2, start=270, extent=90, fill=fill, outline="")
        self.create_rectangle(x1 + r, y1, x2 - r, y2, fill=fill, outline="")
        self.create_rectangle(x1, y1 + r, x2, y2 - r, fill=fill, outline="")

    def _down(self, _):
        self._pressed = True
        self._redraw()

    def _up(self, _):
        if self._pressed:
            self._pressed = False
            self._redraw()
            self._command()
        self._pressed = False

    def _set_hover(self, on):
        self._hover = on
        self._redraw()

    def _redraw(self):
        self.delete("all")
        if self._pressed:
            color = self._darken(self._bg)
        elif self._hover:
            color = self._lighten(self._bg)
        else:
            color = self._bg
        self.create_round_rect(3, 3, self._bw - 3, self._bh - 3,
                               radius=8, fill=color, outline=color)
        self.create_text(
            self._bw // 2, self._bh // 2,
            text=self._text,
            fill=self._fg,
            font=("Arial", 13, "bold"),
            anchor="center",
        )

    def _darken(self, hex_color):
        r, g, b = int(hex_color[1:3], 16), int(hex_color[3:5], 16), int(hex_color[5:7], 16)
        factor = 0.85
        return f"#{int(r*factor):02x}{int(g*factor):02x}{int(b*factor):02x}"

    def _lighten(self, hex_color):
        r, g, b = int(hex_color[1:3], 16), int(hex_color[3:5], 16), int(hex_color[5:7], 16)
        factor = 1.15
        return f"#{min(int(r*factor), 255):02x}{min(int(g*factor), 255):02x}{min(int(b*factor), 255):02x}"


class NumpadButton(tk.Canvas):
    """数字键盘按钮（圆形）"""

    def __init__(self, parent, text, command, size=48):
        super().__init__(
            parent, width=size, height=size,
            bg="#34495E", highlightthickness=0, bd=0,
            cursor="hand2",
        )
        self._text = text
        self._command = command
        self._hover = False
        self._pressed = False

        self._draw()

        self.bind("<Button-1>", self._down)
        self.bind("<ButtonRelease-1>", self._up)
        self.bind("<Enter>", lambda _: self._set_hover(True))
        self.bind("<Leave>", lambda _: self._set_hover(False))

    def _draw(self):
        self.delete("all")
        if self._pressed:
            color = "#2C3E50"
        elif self._hover:
            color = "#4A6278"
        else:
            color = "#34495E"
        self.create_oval(2, 2, 46, 46, fill=color, outline="")
        self.create_text(24, 24, text=self._text, fill="white",
                         font=("Arial", 18, "bold"), anchor="center")

    def _down(self, _):
        self._pressed = True
        self._draw()

    def _up(self, _):
        if self._pressed:
            self._pressed = False
            self._draw()
            self._command()

    def _set_hover(self, on):
        self._hover = on
        self._draw()


# ─────────────────────────────────────────────────────────────────────────────
# 主程序
# ─────────────────────────────────────────────────────────────────────────────

class SudokuApp(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("Sudoku Solver")
        self.configure(bg="#F0F4F8")
        self.resizable(False, False)

        self.entries: list[list[tk.Entry]] = []
        self._is_solved: list[list[bool]] = [[False] * 9 for _ in range(9)]
        # 题目格：用户输入/图片识别/加载来的原始数字，求解后不变
        self._is_puzzle: list[list[bool]] = [[False] * 9 for _ in range(9)]
        self._solving = False

        self._build_ui()

    # ─────────────────────────────────────────────────────────────────────────
    # 界面
    # ─────────────────────────────────────────────────────────────────────────

    def _build_ui(self):

        main = tk.Frame(self, bg="#F0F4F8")
        main.pack(padx=20, pady=16)

        # ── 标题 ──
        hdr = tk.Frame(main, bg="#F0F4F8")
        hdr.pack(pady=(0, 12))
        tk.Label(hdr, text="Sudoku Solver",
                 font=("Arial", 20, "bold"),
                 fg="#1A2332", bg="#F0F4F8").pack()
        tk.Label(hdr, text="输入数字 → 求解",
                 font=("Arial", 11),
                 fg="#5A6A7A", bg="#F0F4F8").pack(pady=(2, 0))

        # ── 按钮行（用 Frame 承接 Canvas 按钮） ──
        btn_frame = tk.Frame(main, bg="#F0F4F8")
        btn_frame.pack(pady=(0, 14))

        FlatButton(btn_frame, "求解", "#27AE60", "white",
                   self._solve_action, width=88, height=46).pack(side="left", padx=5)
        FlatButton(btn_frame, "提示", "#E67E22", "white",
                   self._hint_action, width=88, height=46).pack(side="left", padx=5)
        FlatButton(btn_frame, "检错", "#8E44AD", "white",
                   self._check_action, width=88, height=46).pack(side="left", padx=5)
        FlatButton(btn_frame, "保存题目", "#2980B9", "white",
                   self._save_action, width=88, height=46).pack(side="left", padx=5)
        FlatButton(btn_frame, "加载题目", "#16A085", "white",
                   self._load_action, width=88, height=46).pack(side="left", padx=5)
        FlatButton(btn_frame, "清空", "#95A5A6", "white",
                   self._clear_action, width=88, height=46).pack(side="left", padx=5)

        # ── 9×9 网格 ──
        grid_wrap = tk.Frame(main, bg="#2C3E50", padx=3, pady=3)
        grid_wrap.pack()

        for r in range(9):
            row_entries = []
            for c in range(9):
                px = 4 if c % 3 == 0 else 1
                py = 4 if r % 3 == 0 else 1
                entry = tk.Entry(
                    grid_wrap, width=2,
                    font=("Arial", 24, "bold"),
                    justify="center", bd=1, highlightthickness=0,
                    bg="#FFFFFF", fg="#1A2332",
                    insertbackground="#1A2332",
                )
                entry.grid(row=r, column=c, padx=px, pady=py,
                           ipadx=6, ipady=3, sticky="nsew")
                entry._r = r
                entry._c = c
                entry.bind("<KeyRelease>", self._on_key_release)
                entry.bind("<FocusIn>", self._on_focus_in)
                entry.bind("<FocusOut>", self._on_focus_out)
                entry.bind("<Button-1>", lambda e, en=entry: en.focus_set())
                entry.bind("<Right>", lambda e, en=entry: self._move(en, 1, 0))
                entry.bind("<Left>",  lambda e, en=entry: self._move(en, -1, 0))
                entry.bind("<Up>",    lambda e, en=entry: self._move(en, 0, -1))
                entry.bind("<Down>",  lambda e, en=entry: self._move(en, 0, 1))
                row_entries.append(entry)
            self.entries.append(row_entries)

        # ── 数字键盘 ──
        npad = tk.Frame(main, bg="#F0F4F8")
        npad.pack(pady=(12, 0))

        NumpadButton(npad, "⌫", lambda: self._numpad(0)).pack(side="left", padx=4)
        for n in range(1, 10):
            NumpadButton(npad, str(n), lambda v=n: self._numpad(v)).pack(side="left", padx=4)

        # ── 状态栏 ──
        self._status = tk.Label(
            main, text="在格子里输入数字（1-9），点击「求解」获得完整答案",
            font=("Arial", 11), fg="#5A6A7A", bg="#F0F4F8", pady=8
        )
        self._status.pack()

    # ─────────────────────────────────────────────────────────────────────────
    # 工具
    # ─────────────────────────────────────────────────────────────────────────

    def _set_status(self, msg, color="#5A6A7A"):
        self._status.configure(text=msg, fg=color)

    def _get_board(self):
        return [
            [int(self.entries[r][c].get().strip()) if
             self.entries[r][c].get().strip().isdigit() and
             len(self.entries[r][c].get().strip()) == 1 else 0
             for c in range(9)] for r in range(9)
        ]

    def _set_board(self, board, solved=False, puzzle=None):
        """
        solved=True  : 求解后调用，区分题目格与答案格分别着色
        puzzle       : 9×9 bool 矩阵，puzzle[r][c]==True 表示该格是原始题目数字
        """
        if puzzle is None:
            puzzle = [[False] * 9 for _ in range(9)]
        for r in range(9):
            for c in range(9):
                en = self.entries[r][c]
                v = board[r][c]
                en.delete(0, "end")
                if v != 0:
                    en.insert(0, str(v))
                    if solved and not puzzle[r][c]:
                        # 答案格 → 浅绿
                        en.configure(fg="#27AE60", bg="#F0FBF4")
                        self._is_solved[r][c] = True
                    else:
                        # 题目格 → 浅蓝
                        en.configure(fg="#1A5276", bg="#EBF5FB")
                        self._is_solved[r][c] = False
                else:
                    en.configure(fg="#1A2332", bg="#FFFFFF")
                    self._is_solved[r][c] = False

    def _move(self, entry, dc, dr):
        r, c = entry._r, entry._c
        nc, nr = c + dc, r + dr
        if 0 <= nc < 9 and 0 <= nr < 9:
            self.entries[nr][nc].focus_set()

    def _clear_action(self):
        for r in range(9):
            for c in range(9):
                en = self.entries[r][c]
                en.configure(state="normal")
                en.delete(0, "end")
                en.configure(bg="#FFFFFF", fg="#1A2332")
                self._is_solved[r][c] = False
                self._is_puzzle[r][c] = False
        self._set_status("已清空，输入数字后点击「求解」")

    # ─────────────────────────────────────────────────────────────────────────
    # 求解（后台线程）
    # ─────────────────────────────────────────────────────────────────────────

    def _solve_action(self):
        if self._solving:
            return
        board = self._get_board()
        filled = count_filled(board)
        if filled == 0:
            self._set_status("请先在格子里输入一些数字", "#E67E22")
            return
        errors = check_errors(board)
        if errors:
            self._set_status("输入有冲突，红色格子存在冲突", "#E74C3C")
            for r, c in errors:
                self.entries[r][c].configure(bg="#FDECEA", fg="#C0392B")
            return
        self._solving = True
        self._set_status("求解中…", "#2980B9")

        def worker():
            # 求解前快照题目（用于区分题目格与答案格）
            puzzle = [row[:] for row in self._is_puzzle]
            board_copy = [row[:] for row in board]
            solve(board_copy)

            def done():
                self._solving = False
                self._set_board(board_copy, solved=True, puzzle=puzzle)
                if filled == 81:
                    self._set_status("验证完成，数字全部正确", "#27AE60")
                else:
                    ans = sum(
                        1 for r in range(9) for c in range(9)
                        if board_copy[r][c] != 0 and not puzzle[r][c]
                    )
                    self._set_status(f"求解完成！蓝色为原题，绿色为答案（共填入 {ans} 个数字）", "#27AE60")

            self.after(0, done)

        threading.Thread(target=worker, daemon=True).start()

    # ─────────────────────────────────────────────────────────────────────────
    # 提示
    # ─────────────────────────────────────────────────────────────────────────

    def _hint_action(self):
        if self._solving:
            return
        board = self._get_board()
        board_copy = [row[:] for row in board]
        solve(board_copy)
        empties = [(r, c) for r in range(9) for c in range(9)
                   if board[r][c] == 0 and board_copy[r][c] != 0]
        if not empties:
            fn = count_filled(board)
            self._set_status("已全部填满！" if fn == 81 else "当前无解，无法提示",
                             "#27AE60" if fn == 81 else "#E74C3C")
            return
        r, c = empties[0]
        en = self.entries[r][c]
        en.delete(0, "end")
        en.insert(0, str(board_copy[r][c]))
        en.configure(fg="#27AE60", bg="#F0FBF4")
        self._is_solved[r][c] = True
        self._set_status(f"提示：第 {r+1} 行第 {c+1} 列 → {board_copy[r][c]}", "#27AE60")

    # ─────────────────────────────────────────────────────────────────────────
    # 检错
    # ─────────────────────────────────────────────────────────────────────────

    def _check_action(self):
        if self._solving:
            return
        board = self._get_board()
        errors = check_errors(board)
        for r in range(9):
            for c in range(9):
                en = self.entries[r][c]
                if self._is_solved[r][c]:
                    en.configure(bg="#F0FBF4", fg="#27AE60")
                else:
                    en.configure(bg="#FFFFFF", fg="#1A2332")
        for r, c in errors:
            self.entries[r][c].configure(bg="#FDECEA", fg="#C0392B")
        filled = count_filled(board)
        if errors:
            self._set_status(f"发现 {len(errors)} 个冲突（红色标注）", "#E74C3C")
        else:
            self._set_status("完美！全部正确" if filled == 81 else f"暂无冲突，已填 {filled}/81",
                             "#27AE60" if filled == 81 else "#5A6A7A")

    # ─────────────────────────────────────────────────────────────────────────
    # 输入处理
    # ─────────────────────────────────────────────────────────────────────────

    def _on_key_release(self, event):
        en = event.widget
        val = en.get()
        if len(val) > 1:
            en.delete(1, "end")
            val = en.get()
        if val and val not in "123456789":
            en.delete(0, "end")
            val = ""
        # 手动输入非答案格 → 标记为题目数字；清空则取消标记
        if not self._is_solved[en._r][en._c]:
            if val:
                self._is_puzzle[en._r][en._c] = True
                en.configure(fg="#1A5276", bg="#EBF5FB")
            else:
                self._is_puzzle[en._r][en._c] = False
                en.configure(fg="#1A2332", bg="#FFFFFF")

    def _on_focus_in(self, event):
        en = event.widget
        r, c = en._r, en._c
        for row in self.entries:
            for e in row:
                if self._is_solved[e._r][e._c]:
                    e.configure(bg="#F0FBF4", fg="#27AE60")
                elif self._is_puzzle[e._r][e._c]:
                    e.configure(bg="#EBF5FB", fg="#1A5276")
                else:
                    e.configure(bg="#FFFFFF", fg="#1A2332")
        for k in range(9):
            self._hl(k, c, "#EBF5FB")
            self._hl(r, k, "#EBF5FB")
        br, bc = (r // 3) * 3, (c // 3) * 3
        for dr in range(3):
            for dc in range(3):
                self._hl(br + dr, bc + dc, "#EBF5FB")
        en.configure(bg="#D6EAF8")

    def _on_focus_out(self, event):
        self._reset_bgs()

    def _hl(self, r, c, color):
        en = self.entries[r][c]
        if self._is_solved[r][c]:
            en.configure(bg="#F0FBF4")
        elif self._is_puzzle[r][c]:
            en.configure(bg="#EBF5FB")
        else:
            en.configure(bg=color)

    def _reset_bgs(self):
        for r in range(9):
            for c in range(9):
                en = self.entries[r][c]
                if self._is_solved[r][c]:
                    en.configure(bg="#F0FBF4", fg="#27AE60")
                elif self._is_puzzle[r][c]:
                    en.configure(bg="#EBF5FB", fg="#1A5276")
                else:
                    en.configure(bg="#FFFFFF", fg="#1A2332")

    def _numpad(self, num):
        focused = self.focus_get()
        if not isinstance(focused, tk.Entry):
            for row in self.entries:
                for en in row:
                    if not self._is_solved[en._r][en._c]:
                        focused = en
                        break
                else:
                    continue
                break
        if isinstance(focused, tk.Entry):
            r, c = focused._r, focused._c
            focused.delete(0, "end")
            if num != 0:
                focused.insert(0, str(num))
                if not self._is_solved[r][c]:
                    self._is_puzzle[r][c] = True
                    focused.configure(fg="#1A5276", bg="#EBF5FB")
            else:
                self._is_puzzle[r][c] = False
                focused.configure(fg="#1A2332", bg="#FFFFFF")
            focused.focus_set()

    # ─────────────────────────────────────────────────────────────────────────
    # 保存 / 加载题目
    # ─────────────────────────────────────────────────────────────────────────

    def _save_action(self):
        board = self._get_board()
        puzzle_filled = sum(
            1 for r in range(9) for c in range(9)
            if self._is_puzzle[r][c] and board[r][c] != 0
        )
        if puzzle_filled == 0:
            self._set_status("格子为空，无题目可保存（蓝色数字才算题目）", "#E67E22")
            return
        path = filedialog.asksaveasfilename(
            title="保存数独题目",
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")],
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                for r in range(9):
                    line = "".join(
                        str(board[r][c]) if self._is_puzzle[r][c] else "."
                        for c in range(9)
                    )
                    f.write(line + "\n")
            self._set_status(f"题目已保存至：{path}（{puzzle_filled} 个数字）", "#27AE60")
        except Exception as e:
            messagebox.showerror("保存失败", str(e))

    def _load_action(self):
        path = filedialog.askopenfilename(
            title="加载数独题目",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")],
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                lines = [ln.rstrip("\n") for ln in f.readlines()]
            # 支持 81 字符无换行格式（去空格/换行后拼成一行）
            raw = "".join(lines)
            raw = raw.replace(" ", "").replace("\n", "")
            if len(raw) == 81:
                lines = [raw[i * 9:(i + 1) * 9] for i in range(9)]
            if len(lines) < 9:
                raise ValueError(f"文件内容不足 9 行（实际 {len(lines)} 行）")
            board = []
            for r, line in enumerate(lines[:9]):
                line = line.strip()
                if len(line) != 9:
                    raise ValueError(f"第 {r+1} 行长度不是 9（实际 {len(line)}）")
                row = []
                for ch in line:
                    if ch == "." or ch == "0":
                        row.append(0)
                    elif ch in "123456789":
                        row.append(int(ch))
                    else:
                        raise ValueError(f"第 {r+1} 列含非法字符：{ch!r}")
                board.append(row)
        except Exception as e:
            messagebox.showerror("加载失败", f"文件格式错误：\n{e}")
            return

        self._clear_action()
        # 标记哪些格是题目数字
        for r in range(9):
            for c in range(9):
                if board[r][c] != 0:
                    self._is_puzzle[r][c] = True
        self._set_board(board, solved=False)
        filled = count_filled(board)
        self._set_status(f"已加载题目，蓝色为原题数字（共 {filled} 个）", "#27AE60")


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = SudokuApp()
    app.mainloop()
