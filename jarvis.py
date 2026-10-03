#!/usr/bin/env python3
"""
J.A.R.V.I.S. - Just A Rather Very Intelligent System
A Tony-Stark-style terminal assistant. Pure Python standard library
(psutil is optional for richer stats:  pip install psutil)

Run:  python jarvis.py
"""
import ast
import ipaddress
import json
import math
import operator as op
import os
import platform
import random
import shutil
import socket
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

try:
    import psutil
except ImportError:
    psutil = None

# ---------- ANSI helpers ----------
if os.name == "nt":
    os.system("")  # enable ANSI on Windows terminals

CYAN, RED, GOLD, GREEN, DIM, RST = "\033[96m", "\033[91m", "\033[93m", "\033[92m", "\033[2m", "\033[0m"
CLEAR, HOME, HIDE, SHOW = "\033[2J", "\033[H", "\033[?25l", "\033[?25h"
NOTES = Path.home() / ".jarvis_notes.json"


def c(text, color):
    return f"{color}{text}{RST}"


def say(text):
    """Print like a computer typing + try to speak out loud."""
    for ch in f"[JARVIS] {text}":
        sys.stdout.write(c(ch, CYAN) if ch != "[" else c(ch, GOLD))
        sys.stdout.flush()
        time.sleep(0.012)
    print()


def speak(text):
    try:
        if sys.platform == "darwin":
            subprocess.Popen(["say", text])
        elif shutil.which("espeak"):
            subprocess.Popen(["espeak", text])
        elif os.name == "nt":
            subprocess.Popen(["powershell", "-c",
                              f"Add-Type -AssemblyName System.Speech;"
                              f"(New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak('{text}')"])
        else:
            print(c("(no text-to-speech engine found)", DIM))
    except Exception:
        pass


def bar(pct, width=30):
    pct = max(0, min(100, pct))
    filled = int(width * pct / 100)
    col = GREEN if pct < 60 else GOLD if pct < 85 else RED
    return f"{col}{'█' * filled}{DIM}{'░' * (width - filled)}{RST} {pct:5.1f}%"


# ---------- system stats ----------
def get_stats():
    s = {}
    if psutil:
        s["cpu"] = psutil.cpu_percent(interval=None)
        s["ram"] = psutil.virtual_memory().percent
        s["boot"] = time.time() - psutil.boot_time()
        b = psutil.sensors_battery() if hasattr(psutil, "sensors_battery") else None
        s["bat"] = b.percent if b else None
    else:
        s["cpu"] = (os.getloadavg()[0] / (os.cpu_count() or 1) * 100) if hasattr(os, "getloadavg") else 0
        s["ram"] = 0
        try:
            m = {l.split(":")[0]: int(l.split()[1]) for l in open("/proc/meminfo")}
            s["ram"] = 100 * (1 - m["MemAvailable"] / m["MemTotal"])
        except Exception:
            pass
        s["boot"] = None
        s["bat"] = None
    d = shutil.disk_usage(Path.home())
    s["disk"] = d.used / d.total * 100
    return s


# ---------- features ----------
def boot():
    print(CLEAR + HOME)
    steps = ["Initializing core systems", "Calibrating arc reactor", "Loading neural interface",
             "Establishing secure uplink", "Mounting Mark-VII armor protocols", "Running diagnostics"]
    for st in steps:
        for i in range(0, 101, random.choice([7, 11, 13])):
            sys.stdout.write(f"\r{c('>', GOLD)} {st:<36} {bar(min(i, 100), 24)}")
            sys.stdout.flush()
            time.sleep(0.015)
        sys.stdout.write(f"\r{c('✔', GREEN)} {st:<36} {bar(100, 24)}\n")
    hour = datetime.now().hour
    greet = "morning" if hour < 12 else "afternoon" if hour < 18 else "evening"
    say(f"Good {greet}, sir. All systems online. Type 'help' for commands.")
    speak(f"Good {greet}, sir. All systems online.")


def arc(seconds=6):
    """Animated arc reactor."""
    print(HIDE + CLEAR, end="")
    try:
        t0 = time.time()
        W, H = 61, 27
        while time.time() - t0 < seconds:
            t = time.time() - t0
            grid = [[" "] * W for _ in range(H)]
            cx, cy = W // 2, H // 2

            def plot(x, y, ch, col):
                if 0 <= int(x) < W and 0 <= int(y) < H:
                    grid[int(y)][int(x)] = col + ch + RST

            for r, ch in [(11, "·"), (9, "○"), (6, "◉")]:
                for a in range(0, 360, 3):
                    rad = math.radians(a)
                    plot(cx + math.cos(rad) * r * 2, cy + math.sin(rad) * r, ch, CYAN if r != 9 else DIM + CYAN)
            for k in range(10):  # rotating coil segments
                a = t * 1.6 + k * (2 * math.pi / 10)
                for r in range(3, 9):
                    plot(cx + math.cos(a) * r * 2, cy + math.sin(a) * r, "█", CYAN)
            pulse = "✦" if int(t * 4) % 2 else "★"
            plot(cx, cy, pulse, GOLD)
            sys.stdout.write(HOME + "\n".join("".join(r) for r in grid) +
                             f"\n{c('  ARC REACTOR OUTPUT: ', GOLD)}{c(f'{3000 + 40 * math.sin(t * 3):8.1f} GJ/s', CYAN)}\n")
            sys.stdout.flush()
            time.sleep(0.05)
    except KeyboardInterrupt:
        pass
    finally:
        print(SHOW + CLEAR + HOME, end="")


def hud():
    """Live heads-up display. Ctrl+C to exit."""
    print(HIDE + CLEAR, end="")
    if psutil:
        psutil.cpu_percent(None)
    try:
        while True:
            s = get_stats()
            lines = [
                c("╔══════════════ J.A.R.V.I.S  H U D ══════════════╗", CYAN),
                f"  {c('TIME ', GOLD)} {datetime.now():%Y-%m-%d  %H:%M:%S}",
                f"  {c('HOST ', GOLD)} {platform.node()} ({platform.system()} {platform.release()})",
                "",
                f"  {c('CPU  ', GOLD)} {bar(s['cpu'])}",
                f"  {c('RAM  ', GOLD)} {bar(s['ram'])}",
                f"  {c('DISK ', GOLD)} {bar(s['disk'])}",
            ]
            if s["bat"] is not None:
                lines.append(f"  {c('PWR  ', GOLD)} {bar(s['bat'])}")
            if s["boot"]:
                h, m = divmod(int(s["boot"]) // 60, 60)
                lines.append(f"  {c('UP   ', GOLD)} {h}h {m}m")
            lines += ["", c("╚════════════════ Ctrl+C to exit ═══════════════╝", CYAN)]
            sys.stdout.write(HOME + "\n".join(l + "\033[K" for l in lines))
            sys.stdout.flush()
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        print(SHOW + CLEAR + HOME, end="")


def matrix(seconds=6):
    cols = shutil.get_terminal_size((80, 24))
    w, h = cols.columns, cols.lines - 1
    drops = [random.randint(-h, 0) for _ in range(w)]
    chars = "ﾊﾐﾋｰｳｼﾅﾓﾆｻﾜﾂｵﾘｱﾎﾃﾏｹﾒｴｶｷﾑﾕﾗｾﾈｽﾀﾇﾍ0123456789"
    print(HIDE + CLEAR, end="")
    try:
        t0 = time.time()
        while time.time() - t0 < seconds:
            for x in range(w):
                y = drops[x]
                if 0 <= y < h:
                    sys.stdout.write(f"\033[{y + 1};{x + 1}H{GREEN}{random.choice(chars)}{RST}")
                if 0 <= y - 1 < h:
                    sys.stdout.write(f"\033[{y};{x + 1}H\033[92;2m{random.choice(chars)}{RST}")
                drops[x] += 1
                if drops[x] > h + random.randint(0, 20):
                    drops[x] = 0
            sys.stdout.flush()
            time.sleep(0.04)
    except KeyboardInterrupt:
        pass
    finally:
        print(SHOW + CLEAR + HOME, end="")


def scan(host="127.0.0.1"):
    """Port scan - restricted to loopback/private addresses (your own network)."""
    try:
        ip = ipaddress.ip_address(socket.gethostbyname(host))
    except Exception:
        return say("Cannot resolve that host, sir.")
    if not (ip.is_loopback or ip.is_private):
        return say("I only scan systems on your own network, sir.")
    ports = [21, 22, 23, 25, 53, 80, 110, 143, 443, 445, 3000, 3306, 5000, 5432, 6379, 8000, 8080, 8443, 27017]

    def probe(p):
        with socket.socket() as s:
            s.settimeout(0.4)
            return p if s.connect_ex((str(ip), p)) == 0 else None

    say(f"Scanning {ip} ...")
    with ThreadPoolExecutor(50) as ex:
        found = [p for p in ex.map(probe, ports) if p]
    if found:
        for p in found:
            try:
                name = socket.getservbyport(p)
            except OSError:
                name = "unknown"
            print(f"  {c('OPEN', GREEN)}  {p:<6} {name}")
    else:
        say("No open ports among the common list. Quiet. Suspiciously quiet.")


_OPS = {ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul, ast.Div: op.truediv,
        ast.Pow: op.pow, ast.Mod: op.mod, ast.USub: op.neg, ast.FloorDiv: op.floordiv}
_FUNCS = {k: getattr(math, k) for k in ("sqrt", "sin", "cos", "tan", "log", "log10", "exp", "factorial")}
_FUNCS.update(pi=math.pi, e=math.e)


def _ev(n):
    if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)):
        return n.value
    if isinstance(n, ast.BinOp) and type(n.op) in _OPS:
        return _OPS[type(n.op)](_ev(n.left), _ev(n.right))
    if isinstance(n, ast.UnaryOp) and type(n.op) in _OPS:
        return _OPS[type(n.op)](_ev(n.operand))
    if isinstance(n, ast.Name) and n.id in _FUNCS:
        return _FUNCS[n.id]
    if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in _FUNCS:
        return _FUNCS[n.func.id](*[_ev(a) for a in n.args])
    raise ValueError("unsupported expression")


def calc(expr):
    try:
        say(f"= {_ev(ast.parse(expr, mode='eval').body)}")
    except Exception as e:
        say(f"Calculation failed: {e}")


def timer(secs):
    try:
        secs = int(secs)
    except ValueError:
        return say("Give me seconds, sir. A number.")
    try:
        for r in range(secs, 0, -1):
            sys.stdout.write(f"\r{c('⏱', GOLD)} {r:>4}s  {bar(100 * (secs - r) / secs, 25)}")
            sys.stdout.flush()
            time.sleep(1)
        print(f"\r{c('⏱ Time is up, sir.', RED)}" + " " * 40 + "\a")
        speak("Time is up, sir.")
    except KeyboardInterrupt:
        print()


def notes(args):
    data = json.loads(NOTES.read_text()) if NOTES.exists() else []
    if args[:1] == ["add"] and len(args) > 1:
        data.append({"t": datetime.now().isoformat(timespec="minutes"), "n": " ".join(args[1:])})
        NOTES.write_text(json.dumps(data, ensure_ascii=False, indent=1))
        say("Noted.")
    elif args[:1] == ["clear"]:
        NOTES.write_text("[]")
        say("Notes wiped.")
    else:
        if not data:
            say("No notes on file.")
        for i, d in enumerate(data, 1):
            print(f"  {c(i, GOLD)}. {d['n']}  {c(d['t'], DIM)}")


QUOTES = [
    "Sometimes you gotta run before you can walk.",
    "I am Iron Man.",
    "Genius, billionaire, playboy, philanthropist.",
    "If you're nothing without the suit, then you shouldn't have it.",
    "Part of the journey is the end.",
    "I told you, I don't want to join your super-secret boy band.",
]

HELP = """
  hud            live system dashboard
  arc            arc reactor animation
  matrix         digital rain
  scan [host]    port-scan localhost / your LAN
  calc <expr>    e.g. calc sqrt(144)*pi
  timer <sec>    countdown
  note [add <text> | clear]
  quote          words of wisdom
  say <text>     speak out loud
  clear | exit
"""


def main():
    boot()
    while True:
        try:
            line = input(c("\nJARVIS ❯ ", GOLD)).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not line:
            continue
        cmd, *args = line.split()
        if cmd in ("exit", "quit", "q"):
            say("Powering down. Shall I prep the Mark-VII for tomorrow, sir?")
            break
        elif cmd == "help":
            print(c(HELP, CYAN))
        elif cmd == "hud":
            hud()
        elif cmd == "arc":
            arc()
        elif cmd == "matrix":
            matrix()
        elif cmd == "scan":
            scan(*(args[:1]))
        elif cmd == "calc":
            calc(" ".join(args))
        elif cmd == "timer":
            timer(args[0] if args else "10")
        elif cmd == "note":
            notes(args)
        elif cmd == "quote":
            say(random.choice(QUOTES))
        elif cmd == "say":
            speak(" ".join(args))
        elif cmd == "clear":
            print(CLEAR + HOME, end="")
        else:
            say(f"I don't know '{cmd}', sir. Try 'help'.")


if __name__ == "__main__":
    main()
