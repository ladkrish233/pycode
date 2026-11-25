"""Stdlib-only terminal UI sketch (probe, not pycode code): boxed multiline prompt with history,
streamed line-based markdown, spinner, status line, y/n permission prompt."""
import os, re, sys, shutil, termios, tty, threading, itertools, time

R = "\x1b[0m"; DIM = "\x1b[2m"; B = "\x1b[1m"; IT = "\x1b[3m"; CY = "\x1b[36m"
out = sys.stdout

def _key(fd):
    ch = os.read(fd, 1)
    if ch == b"\x1b":
        # lone ESC vs sequence: only the sequences we need (arrows, alt+enter, home/end)
        nxt = os.read(fd, 1)
        if nxt == b"[":
            s = b""
            while True:
                c = os.read(fd, 1); s += c
                if 0x40 <= c[0] <= 0x7e: break
            return {b"A": "up", b"B": "down", b"C": "right", b"D": "left", b"H": "home", b"F": "end"}.get(s, "?")
        if nxt in (b"\r", b"\n"): return "newline"
        return "?"
    if ch in (b"\r",): return "enter"
    if ch == b"\n": return "newline"
    if ch == b"\x7f": return "bs"
    if ch == b"\x03": return "ctrl-c"
    if ch == b"\x04": return "ctrl-d"
    if ch[0] >= 0x80:  # utf-8 continuation
        n = 1 if ch[0] < 0xe0 else 2 if ch[0] < 0xf0 else 3
        ch += os.read(fd, n)
    return ch.decode("utf-8", "replace")

def read_box(history, status="  ? for shortcuts"):
    """Returns submitted text. Rules above/below, '> ' first line, Alt+Enter/Ctrl+J newline, up/down history."""
    fd = sys.stdin.fileno(); old = termios.tcgetattr(fd); tty.setraw(fd)
    buf, cur, hi, prev_row = "", 0, len(history), 0
    def draw():
        nonlocal prev_row
        w = shutil.get_terminal_size().columns
        lines = buf.split("\n")
        if prev_row: out.write(f"\x1b[{prev_row}A")
        out.write("\r\x1b[J")
        rule = DIM + "─" * w + R
        body = "\r\n".join(("> " if i == 0 else "  ") + l for i, l in enumerate(lines))
        out.write(rule + "\r\n" + body + "\r\n" + rule + "\r\n" + DIM + status + R)
        before = buf[:cur]; row = before.count("\n"); col = 2 + len(before.split("\n")[-1])
        up = (len(lines) - 1 - row) + 2
        out.write(f"\x1b[{up}A\r\x1b[{col}C"); out.flush()
        prev_row = 1 + row
    try:
        draw()
        while True:
            k = _key(fd)
            if k == "enter": break
            elif k == "newline": buf = buf[:cur] + "\n" + buf[cur:]; cur += 1
            elif k == "bs": 
                if cur: buf = buf[:cur-1] + buf[cur:]; cur -= 1
            elif k == "left": cur = max(0, cur-1)
            elif k == "right": cur = min(len(buf), cur+1)
            elif k == "home": cur = 0
            elif k == "end": cur = len(buf)
            elif k == "up" and hi: hi -= 1; buf = history[hi]; cur = len(buf)
            elif k == "down" and hi < len(history): hi += 1; buf = history[hi] if hi < len(history) else ""; cur = len(buf)
            elif k in ("ctrl-c", "ctrl-d"): buf = ""; raise EOFError
            elif len(k) >= 1 and k.isprintable(): buf = buf[:cur] + k + buf[cur:]; cur += len(k)
            else: continue
            draw()
    finally:
        # leave box in scrollback, put cursor below it
        down = (buf.count("\n") - buf[:cur].count("\n")) + 2
        out.write(f"\x1b[{down}B\r\n"); out.flush()
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
    if buf.strip(): history.append(buf)
    return buf

_inl = re.compile(r"(\*\*[^*]+\*\*|`[^`]+`|\*[^*]+\*)")
def _inline(s):
    def f(m):
        t = m.group(0)
        if t.startswith("**"): return B + t[2:-2] + R
        if t.startswith("`"): return CY + t[1:-1] + R
        return IT + t[1:-1] + R
    return _inl.sub(f, s)

class MdStream:
    """Line-buffered markdown: feed(chunk) prints each completed line styled; flush() prints the tail."""
    def __init__(self): self.buf = ""; self.fence = False
    def feed(self, chunk):
        self.buf += chunk
        while "\n" in self.buf:
            line, self.buf = self.buf.split("\n", 1); self._line(line)
    def flush(self):
        if self.buf: self._line(self.buf); self.buf = ""
    def _line(self, l):
        if l.startswith("```"): self.fence = not self.fence; out.write(DIM + l + R + "\n")
        elif self.fence: out.write(CY + "  " + l + R + "\n")
        elif m := re.match(r"(#{1,6})\s+(.*)", l): out.write(B + m.group(2) + R + "\n")
        elif m := re.match(r"(\s*)[-*]\s+(.*)", l): out.write(m.group(1) + "• " + _inline(m.group(2)) + "\n")
        else: out.write(_inline(l) + "\n")
        out.flush()

class Spinner:
    def __init__(self, label="Thinking…"): self.label = label; self._stop = threading.Event()
    def __enter__(self):
        def run():
            for f in itertools.cycle("⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"):
                if self._stop.is_set(): break
                out.write(f"\r{CY}{f}{R} {self.label}\x1b[K"); out.flush(); time.sleep(0.08)
            out.write("\r\x1b[K"); out.flush()
        self.t = threading.Thread(target=run, daemon=True); self.t.start(); return self
    def __exit__(self, *a): self._stop.set(); self.t.join()

def confirm(q):
    fd = sys.stdin.fileno(); old = termios.tcgetattr(fd); tty.setcbreak(fd)
    out.write(f"{B}{q}{R} {DIM}[y/n]{R} "); out.flush()
    try:
        while True:
            c = os.read(fd, 1).lower()
            if c in (b"y", b"n"): out.write(c.decode() + "\n"); return c == b"y"
    finally: termios.tcsetattr(fd, termios.TCSADRAIN, old)
