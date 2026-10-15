"""Generate the DevTools-style network waterfall hero for the GitHub profile.

Writes assets/waterfall-{light,dark}{,-narrow}.svg. Run: python3 tools/waterfall.py

With --prs, the upstream-prs.json row is rebuilt from a `gh search prs --merged
--json repository` dump, so the animation tracks real merged pull requests:

    gh search prs --author jwcastillo --merged --limit 1000 --json repository > prs.json
    python3 tools/waterfall.py --prs prs.json --ignore "jwcastillo/*:MINED-Lidd/*"
"""

import argparse
import json
from collections import Counter
from fnmatch import fnmatch
from pathlib import Path
from xml.sax.saxutils import escape

OUT = Path(__file__).resolve().parent.parent / "assets"

# name, subtitle, status, type, start ms, waiting (TTFB) ms, download ms
REQUESTS = [
    ("wen-castillo.html", "performance engineer · santiago, chile", 200, "document", 0, 22, 16),
    ("hexagonal.css", "clean architecture, test-first", 200, "stylesheet", 46, 30, 22),
    ("core-web-vitals.json", "lcp, inp and cls budgets under load", 200, "fetch", 58, 40, 24),
    ("k6-load-tests.js", "scenarios, thresholds, grafana dashboards", 200, "script", 72, 70, 110),
    ("skillspector.audit", "ai agent skill audits with nvidia skillspector", 200, "fetch", 268, 54, 42),
    ("upstream-prs.json", "merged fixes in nvidia, wshobson, caveman", 201, "fetch", 372, 48, 72),
    ("agent-tooling.md", "claude code · codex · opencode · gemini cli", 200, "other", 452, 36, 40),
    ("say-hi.preconnect", "open to performance work · linkedin below", 101, "other", 690, 64, 36),
]
DCL_MS, LCP_MS, LOAD_MS, FINISH_MS, SCALE_MS = 304, 262, 790, 812, 860

THEMES = {
    "light": dict(
        bg="#ffffff", chrome="#f1f3f4", stripe="#f8f9fa", border="#dadce0", text="#1f1f1f",
        muted="#5f6368", accent="#1a73e8", ttfb="#0f9d58", dl="#1a73e8", queue="#bdc1c6",
        dcl="#1a73e8", load="#d93025", lcp="#0f9d58", rec="#d93025", ok="#1f1f1f",
        redirect="#b06000", track="#eef0f2",
    ),
    "dark": dict(
        bg="#202124", chrome="#292a2d", stripe="#242528", border="#3c4043", text="#e8eaed",
        muted="#9aa0a6", accent="#8ab4f8", ttfb="#34a853", dl="#8ab4f8", queue="#5f6368",
        dcl="#8ab4f8", load="#f28b82", lcp="#81c995", rec="#f28b82", ok="#e8eaed",
        redirect="#fdd663", track="#2a2b2e",
    ),
}

CYCLE = 12.0  # seconds per loop
T0 = 0.7  # seconds before the first request
MS_TO_S = 0.004  # 1 ms of page load = 4 ms of animation
HOLD_END, FADE_END = 90.0, 95.0  # loop percentages


def pct(seconds: float) -> float:
    return round(seconds / CYCLE * 100, 2)


def at(ms: float) -> float:
    return T0 + ms * MS_TO_S


class Anim:
    """Collects one keyframe block per animated element."""

    def __init__(self) -> None:
        self.rules: list[str] = []

    def appear(self, cls: str, start_s: float, dur_s: float = 0.2) -> str:
        a, b = pct(start_s), pct(start_s + dur_s)
        self.rules.append(
            f"@keyframes {cls}{{0%,{a}%{{opacity:0}}{b}%,{HOLD_END}%{{opacity:1}}"
            f"{FADE_END}%,100%{{opacity:0}}}}.{cls}{{animation:{cls} {CYCLE}s linear infinite}}"
        )
        return cls

    def grow(self, cls: str, start_s: float, dur_s: float) -> str:
        a, b = pct(start_s), pct(start_s + max(dur_s, 0.05))
        self.rules.append(
            f"@keyframes {cls}{{0%,{a}%{{transform:scaleX(0)}}{b}%,100%{{transform:scaleX(1)}}}}"
            f".{cls}{{transform-box:fill-box;transform-origin:0 50%;"
            f"animation:{cls} {CYCLE}s cubic-bezier(.16,1,.3,1) infinite}}"
        )
        return cls

    def sweep(self, cls: str, distance: float, start_s: float, end_s: float) -> str:
        a, b, c = pct(start_s), pct(end_s), pct(end_s + 0.3)
        self.rules.append(
            f"@keyframes {cls}{{0%,{a}%{{transform:translateX(0);opacity:1}}"
            f"{b}%{{transform:translateX({distance}px);opacity:1}}{c}%,100%{{transform:translateX({distance}px);opacity:0}}}}"
            f".{cls}{{opacity:0;animation:{cls} {CYCLE}s linear infinite}}"
        )
        return cls

    def blink(self, cls: str) -> str:
        self.rules.append(
            f"@keyframes {cls}{{0%,{pct(at(LOAD_MS))}%{{opacity:1}}{pct(at(LOAD_MS)+.2)}%,{FADE_END}%{{opacity:.35}}100%{{opacity:1}}}}"
            f".{cls}{{animation:{cls} {CYCLE}s linear infinite}}"
        )
        return cls


def text(x, y, s, cls, anchor="start", extra=""):
    return f'<text x="{x}" y="{y}" class="{cls}" text-anchor="{anchor}"{extra}>{escape(s)}</text>'


def build(theme: str, narrow: bool) -> str:
    c = THEMES[theme]
    anim = Anim()
    W = 480 if narrow else 880
    row_h = 40
    top_tabs, toolbar, overview, header = 30, 30, 44, 24
    y_rows = top_tabs + toolbar + overview + header
    status_h = 26
    H = y_rows + row_h * len(REQUESTS) + status_h
    if narrow:
        cols = dict(name=12, time=W - 214, wf=W - 172, wf_w=160)
    else:
        cols = dict(name=12, status=330, type=380, time=488, wf=530, wf_w=W - 542)

    def x_ms(ms: float) -> float:
        return round(cols["wf"] + ms / SCALE_MS * cols["wf_w"], 1)

    out: list[str] = []
    a = out.append

    # Window chrome: panel tabs
    a(f'<rect width="{W}" height="{H}" rx="10" class="bg"/>')
    a(f'<path d="M0 10a10 10 0 0 1 10-10h{W-20}a10 10 0 0 1 10 10v{top_tabs-10}H0z" class="chrome"/>')
    tabs = ["Elements", "Console", "Network", "Performance"] if narrow else [
        "Elements", "Console", "Sources", "Network", "Performance", "Lighthouse"]
    tx = 14
    for t in tabs:
        w = len(t) * 6.6 + 18
        if t == "Network":
            a(f'<rect x="{tx}" y="{top_tabs-2}" width="{w}" height="2" class="accentfill"/>')
        a(text(tx + w / 2, 19, t, "tab on" if t == "Network" else "tab", "middle"))
        tx += w + 2
    a(f'<line x1="0" y1="{top_tabs+.5}" x2="{W}" y2="{top_tabs+.5}" class="rule"/>')

    # Toolbar: record, clear, filter, throttling
    ty = top_tabs + toolbar / 2
    rec = anim.blink("rec")
    a(f'<circle cx="20" cy="{ty}" r="5.5" class="recfill {rec}"/>')
    a(f'<circle cx="42" cy="{ty}" r="5.5" class="icon"/><line x1="38.2" y1="{ty+3.8}" x2="45.8" y2="{ty-3.8}" class="icon"/>')
    a(f'<line x1="60.5" y1="{top_tabs+7}" x2="60.5" y2="{top_tabs+toolbar-7}" class="rule"/>')
    a(f'<path d="M72 {ty-5}h10l-4 5v4l-2 1v-5z" class="icon"/>')
    a(f'<rect x="90" y="{ty-9}" width="{150 if narrow else 190}" height="18" rx="9" class="field"/>')
    a(text(100, ty + 4, "github.com/jwcastillo", "filter"))
    if not narrow:
        a(f'<rect x="300" y="{ty-5.5}" width="11" height="11" rx="2" class="box"/>')
        a(text(318, ty + 4, "Disable cache", "tool"))
        a(text(420, ty + 4, "No throttling", "tool"))
        a(f'<path d="M497 {ty-2}l3.5 4 3.5-4" class="icon"/>')
    a(f'<line x1="0" y1="{top_tabs+toolbar+.5}" x2="{W}" y2="{top_tabs+toolbar+.5}" class="rule"/>')

    # Overview ruler with DCL / LCP / Load markers
    oy = top_tabs + toolbar
    ruler_x0, ruler_w = 12, W - 24
    def rx(ms):
        return round(ruler_x0 + ms / SCALE_MS * ruler_w, 1)
    step = 200 if narrow else 100
    for ms in range(step, SCALE_MS, step):
        a(f'<line x1="{rx(ms)}" y1="{oy+4}" x2="{rx(ms)}" y2="{oy+overview}" class="tick"/>')
        a(text(rx(ms) - 4, oy + 14, f"{ms} ms", "ruler", "end"))
    for i, (_, _, _, kind, start, ttfb, dl) in enumerate(REQUESTS):
        yy = oy + 18 + (i % 4) * 3.5
        g = anim.grow(f"ov{i}", at(start), (ttfb + dl) * MS_TO_S)
        a(f'<rect x="{rx(start)}" y="{yy}" width="{max(rx(start+ttfb+dl)-rx(start),2)}" height="3" rx="1.5" class="dlfill {g}"/>')
    for label, ms, cls in (("DCL", DCL_MS, "dcl"), ("LCP", LCP_MS, "lcp"), ("Load", LOAD_MS, "load")):
        m = anim.appear(f"m{cls}", at(ms))
        left = cls == "lcp"  # LCP sits just before DCL: label it on the left so they never collide
        a(f'<g class="{m}"><line x1="{rx(ms)}" y1="{oy+18}" x2="{rx(ms)}" y2="{oy+overview}" class="{cls}line"/>'
          f'{text(rx(ms) + (-4 if left else 4), oy+overview-3, label, cls + "txt", "end" if left else "start")}</g>')
    a(f'<line x1="0" y1="{oy+overview+.5}" x2="{W}" y2="{oy+overview+.5}" class="rule"/>')

    # Table header
    hy = oy + overview
    a(f'<rect x="0" y="{hy+1}" width="{W}" height="{header-1}" class="chrome"/>')
    a(text(cols["name"], hy + 16, "Name", "th"))
    if not narrow:
        a(text(cols["status"], hy + 16, "Status", "th"))
        a(text(cols["type"], hy + 16, "Type", "th"))
    a(text(cols["time"] + (32 if not narrow else 0), hy + 16, "Time", "th", "end" if not narrow else "start"))
    a(text(cols["wf"], hy + 16, "Waterfall", "th"))
    a(f'<line x1="0" y1="{hy+header+.5}" x2="{W}" y2="{hy+header+.5}" class="rule"/>')
    for key in ("status", "type", "time", "wf"):
        if key in cols:
            a(f'<line x1="{cols[key]-8.5}" y1="{hy}" x2="{cols[key]-8.5}" y2="{H-status_h}" class="colrule"/>')

    # Waterfall grid lines and timing markers, drawn under the rows
    for ms in range(step, SCALE_MS, step):
        a(f'<line x1="{x_ms(ms)}" y1="{y_rows}" x2="{x_ms(ms)}" y2="{H-status_h}" class="grid"/>')
    for ms, cls in ((DCL_MS, "dcl"), (LOAD_MS, "load")):
        m = anim.appear(f"g{cls}", at(ms))
        a(f'<line x1="{x_ms(ms)}" y1="{y_rows}" x2="{x_ms(ms)}" y2="{H-status_h}" class="{cls}line {m}"/>')

    # Request rows
    for i, (name, sub, status, kind, start, ttfb, dl) in enumerate(REQUESTS):
        y = y_rows + i * row_h
        if i % 2:
            a(f'<rect x="0" y="{y}" width="{W}" height="{row_h}" class="stripe"/>')
        # Ghost track: the slot is drawn before the request arrives
        a(f'<rect x="{x_ms(start)}" y="{y+row_h/2-4}" width="{x_ms(start+ttfb+dl)-x_ms(start)}" height="8" rx="2" class="track"/>')
        r = anim.appear(f"r{i}", at(start))
        a(f'<g class="{r}">')
        icon_cls = {"document": "dcl", "stylesheet": "lcp", "script": "load"}.get(kind, "muted")
        a(f'<rect x="{cols["name"]}" y="{y+row_h/2-6}" width="10" height="12" rx="1.5" class="kind {icon_cls}stroke"/>')
        a(text(cols["name"] + 18, y + 17, name, "name"))
        a(text(cols["name"] + 18, y + 31, sub, "sub"))
        if not narrow:
            a(text(cols["status"], y + 24, str(status), "cell" if status == 200 else "cell warn"))
            a(text(cols["type"], y + 24, kind, "cell"))
            a(text(cols["time"] + 32, y + 24, f"{ttfb+dl} ms", "cell", "end"))
        else:
            a(text(cols["time"], y + 24, f"{ttfb+dl}", "cell"))
        a("</g>")
        bx, by = x_ms(start), y + row_h / 2 - 4
        wq = x_ms(start + ttfb) - bx
        wd = x_ms(start + ttfb + dl) - x_ms(start + ttfb)
        g1 = anim.grow(f"t{i}", at(start), ttfb * MS_TO_S)
        g2 = anim.grow(f"d{i}", at(start + ttfb), dl * MS_TO_S)
        a(f'<rect x="{bx}" y="{by}" width="{wq}" height="8" rx="2" class="ttfbfill {g1}"/>')
        a(f'<rect x="{bx+wq}" y="{by}" width="{wd}" height="8" rx="2" class="dlfill {g2}"/>')

    # Playhead sweeping the waterfall while the page loads
    ph = anim.sweep("ph", x_ms(LOAD_MS) - x_ms(0), T0, at(LOAD_MS))
    a(f'<line x1="{x_ms(0)}" y1="{y_rows}" x2="{x_ms(0)}" y2="{H-status_h}" class="playhead {ph}"/>')

    # Status bar
    sy = H - status_h
    a(f'<path d="M0 {sy}h{W}v{status_h-10}a10 10 0 0 1-10 10H10a10 10 0 0 1-10-10z" class="chrome"/>')
    a(f'<line x1="0" y1="{sy+.5}" x2="{W}" y2="{sy+.5}" class="rule"/>')
    s1 = anim.appear("s1", T0)
    s2 = anim.appear("s2", at(FINISH_MS))
    a(text(12, sy + 17, f"{len(REQUESTS)} requests", f"statusbar {s1}"))
    summary = (f"Finish: {FINISH_MS} ms" if narrow else
               f"Finish: {FINISH_MS} ms  |  DOMContentLoaded: {DCL_MS} ms  |  Load: {LOAD_MS} ms")
    a(text(W - 12, sy + 17, summary, f"statusbar {s2}", "end"))

    css = f"""
text{{font-family:"Segoe UI",system-ui,-apple-system,BlinkMacSystemFont,Roboto,"Helvetica Neue",Arial,sans-serif;font-variant-numeric:tabular-nums}}
.bg{{fill:{c['bg']};stroke:{c['border']}}}.chrome{{fill:{c['chrome']}}}.stripe{{fill:{c['stripe']}}}
.rule{{stroke:{c['border']};stroke-width:1}}.colrule{{stroke:{c['border']};stroke-width:1;opacity:.6}}
.grid{{stroke:{c['border']};stroke-width:1;opacity:.45}}.tick{{stroke:{c['border']};stroke-width:1;opacity:.7}}
.tab{{font-size:12px;fill:{c['muted']}}}.tab.on{{fill:{c['text']};font-weight:600}}.accentfill{{fill:{c['accent']}}}
.icon{{fill:none;stroke:{c['muted']};stroke-width:1.4;stroke-linecap:round;stroke-linejoin:round}}
.recfill{{fill:{c['rec']}}}.field{{fill:{c['bg']};stroke:{c['border']}}}.box{{fill:none;stroke:{c['muted']}}}
.filter{{font-size:11.5px;fill:{c['text']}}}.tool{{font-size:11.5px;fill:{c['muted']}}}
.ruler{{font-size:10px;fill:{c['muted']}}}.th{{font-size:11.5px;font-weight:600;fill:{c['text']}}}
.name{{font-size:12.5px;font-weight:600;fill:{c['text']}}}.sub{{font-size:11px;fill:{c['muted']}}}
.cell{{font-size:12px;fill:{c['ok']}}}.warn{{fill:{c['redirect']}}}.statusbar{{font-size:11.5px;fill:{c['muted']}}}
.kind{{fill:none;stroke-width:1.4}}.dclstroke{{stroke:{c['dcl']}}}.lcpstroke{{stroke:{c['lcp']}}}.loadstroke{{stroke:{c['load']}}}.mutedstroke{{stroke:{c['muted']}}}
.track{{fill:{c['track']}}}.ttfbfill{{fill:{c['ttfb']}}}.dlfill{{fill:{c['dl']}}}
.dclline{{stroke:{c['dcl']};stroke-width:1.5}}.loadline{{stroke:{c['load']};stroke-width:1.5}}.lcpline{{stroke:{c['lcp']};stroke-width:1.5;stroke-dasharray:3 3}}
.dcltxt{{font-size:10px;font-weight:600;fill:{c['dcl']}}}.loadtxt{{font-size:10px;font-weight:600;fill:{c['load']}}}.lcptxt{{font-size:10px;font-weight:600;fill:{c['lcp']}}}
.playhead{{stroke:{c['accent']};stroke-width:1.5}}
{''.join(anim.rules)}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}.ph{{opacity:0}}}}
"""
    title = "Wen Castillo's GitHub profile loading as a Chrome DevTools network waterfall"
    desc = "; ".join(f"{n}: {s}" for n, s, *_ in REQUESTS)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
        f'role="img" aria-labelledby="t d"><title id="t">{escape(title)}</title><desc id="d">{escape(desc)}</desc>'
        f"<style>{css}</style>{''.join(out)}</svg>\n"
    )


SUBTITLE_MAX = 46  # longest subtitle that fits the narrow variant


def upstream_subtitle(prs: list[dict], ignore: str) -> str:
    """Summarize merged PRs outside ignored repos, e.g. '9 merged PRs · agents, caveman'."""
    patterns = [p for p in ignore.split(":") if p]
    repos = Counter(
        pr["repository"]["nameWithOwner"]
        for pr in prs
        if not any(fnmatch(pr["repository"]["nameWithOwner"], p) for p in patterns)
    )
    count = sum(repos.values())
    text = f"{count} merged PR{'' if count == 1 else 's'}"
    names: list[str] = []
    for repo, _ in repos.most_common():
        candidate = text + " · " + ", ".join(names + [repo.split("/")[1].lower()])
        if len(candidate) > SUBTITLE_MAX:
            break
        names.append(repo.split("/")[1].lower())
    return text + (" · " + ", ".join(names) if names else "")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--prs", type=Path, help="gh search prs --json repository output")
    parser.add_argument("--ignore", default="", help="colon-separated owner/repo globs to skip")
    args = parser.parse_args()
    if args.prs:
        subtitle = upstream_subtitle(json.loads(args.prs.read_text()), args.ignore)
        REQUESTS = [
            (n, subtitle, *rest) if n == "upstream-prs.json" else (n, sub, *rest)
            for n, sub, *rest in REQUESTS
        ]
    OUT.mkdir(exist_ok=True)
    for theme in THEMES:
        for narrow in (False, True):
            path = OUT / f"waterfall-{theme}{'-narrow' if narrow else ''}.svg"
            path.write_text(build(theme, narrow), encoding="utf-8")
            print(path.name, path.stat().st_size)
