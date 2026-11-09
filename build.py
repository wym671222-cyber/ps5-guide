#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把 data.json 渲染成单文件 HTML 实操步骤页。
只改 data.json，不要手改 index.html。
"""
import html
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = json.loads((HERE / "data.json").read_text(encoding="utf-8"))


def inline(s: str) -> str:
    """先转义，再还原 **bold** 与 `code`。"""
    s = html.escape(s, quote=False)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"`(.+?)`", r"<code>\1</code>", s)
    return s


def ul(items, cls=""):
    if not items:
        return ""
    lis = "".join(f"<li>{inline(x)}</li>" for x in items)
    return f'<ul class="{cls}">{lis}</ul>'


def ol(items):
    lis = "".join(f"<li>{inline(x)}</li>" for x in items)
    return f'<ol class="do-list">{lis}</ol>'


def params_block(items):
    if not items:
        return ""
    rows = []
    for it in items:
        k = html.escape(it["k"], quote=False)
        v = (it.get("v") or "").strip()
        fid = "f_" + re.sub(r"\W+", "_", it["k"])[:24] + "_" + str(abs(hash(it["k"])) % 9999)
        if v:
            val = f'<span class="pv-val">{inline(v)}</span>'
        else:
            val = f'<input class="pv-input" data-field="{fid}" type="text" placeholder="填这里">'
        rows.append(f'<div class="pv"><span class="pv-k">{k}</span>{val}</div>')
    return '<div class="params">' + "".join(rows) + "</div>"


def note_block(kind, label, body):
    if not body:
        return ""
    return (
        f'<div class="note note-{kind}"><span class="note-tag">{label}</span>'
        f'<div class="note-body">{inline(body)}</div></div>'
    )


MIRROR_OPTIONS = [
    ("a", "低于 12.20（但**不是** 11.40）", "用 **4.03** 这份镜像。"),
    ("b", "正好是 **11.40**", "**停手。** 4.03 那一档明确写着「11.40 不支持」，而视频没有给 11.40 的其他路径。"),
    ("c", "12.20 – 13.40", "用 **12.20** 这份镜像。作者的机器 12.4 就落在这一档。"),
    ("d", "13.40 – 13.60", "用 **13.40** 这份镜像。"),
    ("e", "高于 13.6", "**停手。** 超出当前公开方案范围。作者提到「14.1 听说大神也搞定了，但暂时没看到公开」——没公开就等于没有。"),
]


def mirror_selector():
    opts = "".join(
        f'<label class="opt"><input type="radio" name="mirror" value="{v}">'
        f'<span class="opt-txt">{inline(t)}</span></label>'
        for v, t, _ in MIRROR_OPTIONS
    )
    mapping = json.dumps({v: r for v, _, r in MIRROR_OPTIONS}, ensure_ascii=False)
    return (
        '<div class="selector" id="mirrorSel">'
        '<div class="sel-head">你的系统版本落在哪一档？</div>'
        f'<div class="opts">{opts}</div>'
        '<div class="sel-out" id="mirrorOut" hidden></div>'
        f'<script type="application/json" id="mirrorMap">{mapping}</script>'
        "</div>"
    )


def step_html(st, phase_code):
    sid = st["id"]
    parts = [
        f'<article class="step" id="{sid}" data-step="{sid}">',
        f'<div class="step-no" aria-hidden="true">{st["no"]}</div>',
        '<div class="step-head">',
        f'<h3 class="step-title">{inline(st["title"])}</h3>',
        f'<span class="step-time">{html.escape(st["time"])}</span>',
        f'<button class="check" data-check="{sid}" aria-pressed="false" title="标记这一步做完">'
        '<span class="ck-box"></span><span class="ck-txt">做完了</span></button>',
        "</div>",
    ]
    if st.get("lead"):
        parts.append(f'<p class="step-lead">{inline(st["lead"])}</p>')
    if st.get("selector") == "mirror":
        parts.append(mirror_selector())
    parts.append(ol(st["do"]))
    if st.get("proof"):
        parts.append(note_block("ok", "做完确认", st["proof"]))
    parts.append(params_block(st.get("params")))
    if st.get("stuck"):
        parts.append(
            '<div class="note note-warn"><span class="note-tag">卡住了怎么办</span>'
            f'<div class="note-body">{ul(st["stuck"], "stuck-list")}</div></div>'
        )
    parts.append(note_block("risk", "注意", st.get("warn", "")))
    parts.append("</article>")
    return "\n".join(p for p in parts if p)


def table_html(t):
    head = "".join(f"<th>{inline(h)}</th>" for h in t["head"])
    body = ""
    for r in t["rows"]:
        body += "<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>"
    foot = f'<p class="tbl-foot">{inline(t["foot"])}</p>' if t.get("foot") else ""
    return (
        f'<div class="tool" id="tool-{t["id"]}">'
        f'<div class="tool-head"><h3>{inline(t["title"])}</h3>'
        f'<p>{inline(t["desc"])}</p></div>'
        f'<div class="tbl-wrap"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'
        f"{foot}</div>"
    )


def build():
    m = DATA["meta"]
    phases = DATA["phases"]
    total = sum(len(p["steps"]) for p in phases)

    # 侧栏（移动端折叠）
    side = [
        '<div class="side-col">',
        '<button class="side-toggle" id="sideToggle" aria-expanded="false" aria-controls="side">'
        f'<span>步骤导航 · 共 {total} 步</span><span class="tg-state">展开</span></button>',
        '<nav class="side" id="side" aria-label="步骤导航">',
    ]
    for p in phases:
        side.append(f'<div class="side-g"><div class="side-gname"><b>{p["code"]}</b>{html.escape(p["name"])}</div><ol>')
        for s in p["steps"]:
            side.append(
                f'<li><a href="#{s["id"]}" data-nav="{s["id"]}">'
                f'<span class="nav-no">{s["no"]}</span>'
                f'<span class="nav-txt">{html.escape(re.sub(r"[*`]", "", s["title"]))}</span></a></li>'
            )
        side.append("</ol></div>")
    side.append("</nav></div>")

    # 主体
    main = []
    main.append('<section class="intro">')
    main.append('<h2 class="sec-h">怎么用这一页</h2>')
    main.append(
        '<div class="howto">'
        '<div class="how"><b>1</b>按顺序做，别跳。第 0 步不过关卡，后面全部作废。</div>'
        '<div class="how"><b>2</b>每步先看「做什么」，做完对「做完确认」——对不上就别往下走。</div>'
        '<div class="how"><b>3</b>勾选会存在这台设备上，下次打开自动恢复进度。</div>'
        f'<div class="how"><b>4</b>共 {total} 步。{inline(m["expect"])}</div>'
        "</div>"
    )
    main.append("</section>")

    for p in phases:
        main.append(f'<section class="phase" id="{p["id"]}">')
        main.append(
            f'<div class="phase-head"><span class="phase-code">{p["code"]}</span>'
            f'<h2>{html.escape(p["name"])}</h2></div>'
            f'<p class="phase-desc">{inline(p["desc"])}</p>'
        )
        for s in p["steps"]:
            main.append(step_html(s, p["code"]))
        main.append("</section>")

    # 工具区
    main.append('<section class="phase" id="tools">')
    main.append('<div class="phase-head"><span class="phase-code">T</span><h2>两张对照表</h2></div>'
                '<p class="phase-desc">动手时会反复回来查的两张表。建议打印或截图存手机。</p>')
    for t in DATA["tables"]:
        main.append(table_html(t))
    main.append("</section>")

    # 排错
    main.append('<section class="phase" id="fix">')
    main.append('<div class="phase-head"><span class="phase-code">?</span><h2>卡住了先查这里</h2></div>'
                '<p class="phase-desc">按症状找，别一处一处试。</p>')
    rows = "".join(
        f"<tr><td><b>{inline(a)}</b></td><td>{inline(b)}</td><td class='nowrap'>{inline(c)}</td></tr>"
        for a, b, c in DATA["troubleshoot"]
    )
    main.append(
        '<div class="tool"><div class="tbl-wrap"><table>'
        "<thead><tr><th>症状</th><th>怎么处理</th><th>在哪一步</th></tr></thead>"
        f"<tbody>{rows}</tbody></table></div></div>"
    )
    main.append("</section>")

    # 成本
    main.append('<section class="phase" id="cost">')
    main.append('<div class="phase-head"><span class="phase-code">!</span><h2>没算的那笔账</h2></div>'
                '<p class="phase-desc">视频里没做成本核算。做完再决定值不值。</p>')
    rows = "".join(
        f"<tr><td><b>{inline(a)}</b></td><td>{inline(b)}</td><td class='nowrap'>{inline(c)}</td></tr>"
        for a, b, c in DATA["costs"]
    )
    main.append(
        '<div class="tool"><div class="tbl-wrap"><table>'
        "<thead><tr><th>项</th><th>代价</th><th>性质</th></tr></thead>"
        f"<tbody>{rows}</tbody></table></div></div>"
    )
    main.append(
        '<div class="note note-risk" style="margin-top:16px">'
        '<span class="note-tag">红线</span><div class="note-body">'
        f'{inline(DATA["meta"]["redline"])}</div></div>'
    )
    main.append("</section>")

    body = "\n".join(side + ['<main class="main">'] + main + ["</main>"])

    verify = "　·　".join(
        f'<a href="{html.escape(v["url"])}" target="_blank" rel="noopener">'
        f'{html.escape(v["title"])}</a>'
        for v in m.get("verifySources") or []
    ) or "—"

    html_out = TEMPLATE.format(
        title=html.escape(m["title"]),
        subtitle=html.escape(m["subtitle"]),
        total=total,
        body=body,
        source_title=html.escape(m["sourceTitle"]),
        source_url=m["sourceUrl"],
        source_date=m["sourceDate"],
        duration=m["duration"],
        built=m["built"],
        note=inline(m["note"]),
        verify=verify,
    )
    (HERE / "index.html").write_text(html_out, encoding="utf-8")
    print(f"ok -> index.html  ({len(html_out):,} chars, {total} steps)")


TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<style>
:root{{
  --bg:#f5f7fa; --card:#fff; --line:#e2e6eb; --text:#15181c; --muted:#5f6873;
  --accent:#0070d1; --accent-soft:#e9f2fc;
  --ok:#0c7a4a; --ok-soft:#e9f7f0; --ok-line:#bfe6d2;
  --warn:#a15a08; --warn-soft:#fdf4e5; --warn-line:#f3ddb6;
  --risk:#b0392a; --risk-soft:#fdeeec; --risk-line:#f4cdc6;
  --shadow:0 1px 2px rgba(16,24,40,.05),0 8px 24px -12px rgba(16,24,40,.12);
}}
@media (prefers-color-scheme:dark){{
  :root{{
    --bg:#0e1013; --card:#171a1f; --line:#272c34; --text:#e7eaee; --muted:#98a1ac;
    --accent:#57a8f2; --accent-soft:#12283c;
    --ok:#54cb92; --ok-soft:#12261c; --ok-line:#1f4a36;
    --warn:#e2a45f; --warn-soft:#2a2115; --warn-line:#4a3a22;
    --risk:#ea7f69; --risk-soft:#2b1816; --risk-line:#4d2a24;
    --shadow:0 1px 2px rgba(0,0,0,.4),0 8px 24px -12px rgba(0,0,0,.6);
  }}
}}
*{{box-sizing:border-box}}
html{{scroll-behavior:smooth}}
body{{
  margin:0; background:var(--bg); color:var(--text);
  font:15px/1.72 -apple-system,BlinkMacSystemFont,"PingFang SC","Hiragino Sans GB","Microsoft YaHei",system-ui,sans-serif;
  -webkit-font-smoothing:antialiased;
}}
code{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:.9em;
  background:var(--accent-soft); color:var(--accent); padding:1px 5px; border-radius:4px;
  word-break:break-word}}
strong{{font-weight:650;color:var(--text)}}

/* header */
header{{position:sticky;top:0;z-index:50;background:color-mix(in srgb,var(--bg) 86%,transparent);
  backdrop-filter:saturate(180%) blur(14px);border-bottom:1px solid var(--line)}}
.hd{{max-width:1180px;margin:0 auto;padding:12px 20px;display:flex;align-items:center;gap:18px}}
.hd-t{{min-width:0;flex:1 1 auto}}
.hd-t h1{{margin:0;font-size:16px;font-weight:680;letter-spacing:-.01em;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.hd-t p{{margin:1px 0 0;font-size:12px;color:var(--muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.prog{{display:flex;align-items:center;gap:10px;flex:0 0 auto}}
.bar{{width:150px;height:6px;border-radius:99px;background:var(--line);overflow:hidden}}
.bar i{{display:block;height:100%;width:0;background:var(--accent);border-radius:99px;transition:width .25s ease}}
.pnum{{font:600 12px/1 ui-monospace,monospace;color:var(--muted);white-space:nowrap;font-variant-numeric:tabular-nums}}
.reset,.jump{{border:1px solid var(--line);background:var(--card);color:var(--muted);font-size:12px;
  padding:5px 10px;border-radius:7px;cursor:pointer;white-space:nowrap;flex:0 0 auto}}
.reset:hover{{color:var(--text);border-color:var(--muted)}}
.jump{{border-color:var(--accent);background:var(--accent-soft);color:var(--accent);font-weight:600}}
.jump:hover{{background:var(--accent);color:#fff;border-color:var(--accent)}}
.jump[hidden]{{display:none}}

/* layout */
.layout{{max-width:1180px;margin:0 auto;padding:26px 20px 80px;display:grid;
  grid-template-columns:264px minmax(0,1fr);gap:26px;align-items:start}}
.main{{padding-left:18px;min-width:0}}
.side-col{{position:sticky;top:78px;min-width:0}}
.side{{max-height:calc(100vh - 100px);overflow:auto;font-size:13px;padding-right:6px}}
.side-toggle{{display:none}}
.side-g{{margin-bottom:16px}}
.side-gname{{display:flex;align-items:center;gap:7px;color:var(--muted);font-weight:600;
  font-size:11.5px;letter-spacing:.02em;margin-bottom:6px;padding-left:2px}}
.side-gname b{{display:inline-grid;place-items:center;min-width:16px;height:16px;padding:0 3px;
  border-radius:4px;background:var(--line);color:var(--text);font:600 10px/1 ui-monospace,monospace}}
.side ol{{list-style:none;margin:0;padding:0}}
.side a{{display:flex;gap:8px;padding:5px 7px;border-radius:6px;color:var(--muted);
  text-decoration:none;line-height:1.45;border-left:2px solid transparent}}
.side a:hover{{background:var(--card);color:var(--text)}}
.side a.on{{color:var(--accent);background:var(--accent-soft);border-left-color:var(--accent)}}
.side a.done .nav-txt{{color:var(--muted);text-decoration:line-through;text-decoration-thickness:1px}}
.side a.done .nav-no::after{{content:"✓";color:var(--ok);margin-left:2px;font-weight:700}}
.nav-no{{font:600 11px/1.7 ui-monospace,monospace;opacity:.75;flex:0 0 auto}}

/* intro */
.sec-h{{font-size:13px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);
  margin:0 0 12px;font-weight:650}}
.intro{{margin-bottom:34px}}
.howto{{display:grid;grid-template-columns:repeat(2,1fr);gap:10px}}
.how{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 14px;
  font-size:13.5px;color:var(--muted);display:flex;gap:10px;align-items:flex-start;box-shadow:var(--shadow)}}
.how b{{flex:0 0 auto;width:19px;height:19px;border-radius:50%;background:var(--accent-soft);
  color:var(--accent);display:grid;place-items:center;font:600 11px/1 ui-monospace,monospace;margin-top:2px}}

/* phase */
.phase{{margin-bottom:44px;scroll-margin-top:80px}}
.phase-head{{display:flex;align-items:center;gap:11px;margin-bottom:4px}}
.phase-code{{flex:0 0 auto;width:26px;height:26px;border-radius:7px;background:var(--text);color:var(--bg);
  display:grid;place-items:center;font:700 12px/1 ui-monospace,monospace}}
.phase-head h2{{margin:0;font-size:19px;font-weight:680;letter-spacing:-.015em}}
.phase-desc{{margin:0 0 18px 37px;color:var(--muted);font-size:13.5px}}

/* step */
.step{{position:relative;background:var(--card);border:1px solid var(--line);border-radius:13px;
  padding:20px 22px 18px;margin-bottom:14px;box-shadow:var(--shadow);scroll-margin-top:78px;
  transition:border-color .2s,opacity .2s}}
.step.done{{border-color:var(--ok-line)}}
.step.done .step-no{{background:var(--ok);border-color:var(--ok);color:#fff}}
.step-no{{position:absolute;left:-13px;top:19px;width:27px;height:27px;border-radius:50%;
  background:var(--card);border:1px solid var(--line);display:grid;place-items:center;
  font:700 11px/1 ui-monospace,monospace;color:var(--muted);transition:.2s}}
.step-head{{display:flex;align-items:baseline;gap:10px;flex-wrap:wrap;margin-bottom:2px}}
.step-title{{margin:0;font-size:16.5px;font-weight:670;letter-spacing:-.01em;flex:1 1 auto;min-width:0}}
.step-time{{flex:0 0 auto;font-size:11.5px;color:var(--muted);background:var(--bg);
  border:1px solid var(--line);border-radius:99px;padding:2px 9px;white-space:nowrap}}
.check{{flex:0 0 auto;display:inline-flex;align-items:center;gap:6px;border:1px solid var(--line);
  background:var(--card);color:var(--muted);border-radius:99px;padding:4px 11px 4px 8px;
  font:500 12px/1.4 inherit;cursor:pointer;transition:.16s}}
.check:hover{{border-color:var(--ok);color:var(--ok)}}
.ck-box{{width:13px;height:13px;border-radius:4px;border:1.5px solid currentColor;display:inline-block;position:relative}}
.check[aria-pressed="true"]{{background:var(--ok-soft);border-color:var(--ok-line);color:var(--ok)}}
.check[aria-pressed="true"] .ck-box{{background:var(--ok);border-color:var(--ok)}}
.check[aria-pressed="true"] .ck-box::after{{content:"";position:absolute;left:3.5px;top:1px;width:4px;height:7px;
  border:1.6px solid #fff;border-top:0;border-left:0;transform:rotate(42deg)}}
.step-lead{{margin:6px 0 14px;color:var(--muted);font-size:13.5px}}

.do-list{{margin:0 0 14px;padding:0;list-style:none;counter-reset:d}}
.do-list li{{counter-increment:d;position:relative;padding-left:26px;margin-bottom:8px;font-size:14.2px}}
.do-list li::before{{content:counter(d);position:absolute;left:0;top:2px;width:18px;height:18px;
  border-radius:5px;background:var(--accent-soft);color:var(--accent);display:grid;place-items:center;
  font:600 10.5px/1 ui-monospace,monospace}}

/* notes */
.note{{border-radius:9px;padding:11px 13px;margin:0 0 12px;border:1px solid;font-size:13.5px}}
.note-tag{{display:inline-block;font-weight:680;font-size:11.5px;letter-spacing:.03em;margin-bottom:3px}}
.note p{{margin:0}}
.note-ok{{background:var(--ok-soft);border-color:var(--ok-line);color:var(--text)}}
.note-ok .note-tag{{color:var(--ok)}}
.note-warn{{background:var(--warn-soft);border-color:var(--warn-line)}}
.note-warn .note-tag{{color:var(--warn)}}
.note-risk{{background:var(--risk-soft);border-color:var(--risk-line)}}
.note-risk .note-tag{{color:var(--risk)}}
.stuck-list{{margin:5px 0 0;padding-left:17px}}
.stuck-list li{{margin-bottom:4px}}
.stuck-list li::marker{{color:var(--warn)}}

/* params */
.params{{display:grid;gap:6px;margin:0 0 12px;padding:11px 13px;border:1px dashed var(--line);
  border-radius:9px;background:color-mix(in srgb,var(--bg) 60%,var(--card))}}
.pv{{display:flex;align-items:center;gap:10px;font-size:13px}}
.pv-k{{flex:0 0 auto;min-width:104px;color:var(--muted);font-size:12.5px}}
.pv-val{{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12.8px;
  background:var(--accent-soft);color:var(--accent);padding:2px 7px;border-radius:5px;
  -webkit-user-select:all;user-select:all}}
.pv-input{{flex:1 1 auto;min-width:0;background:var(--card);border:1px solid var(--line);
  border-radius:6px;padding:5px 9px;color:var(--text);font:13px/1.4 inherit}}
.pv-input:focus{{outline:none;border-color:var(--accent);box-shadow:0 0 0 3px var(--accent-soft)}}

/* selector */
.selector{{margin:0 0 15px;padding:14px 15px;border:1px solid var(--accent);border-radius:10px;
  background:var(--accent-soft)}}
.sel-head{{font-weight:660;font-size:13.5px;margin-bottom:9px;color:var(--text)}}
.opts{{display:grid;gap:5px}}
.opt{{display:flex;align-items:center;gap:9px;padding:6px 9px;border-radius:7px;cursor:pointer;
  background:var(--card);border:1px solid transparent;font-size:13.5px}}
.opt:hover{{border-color:var(--accent)}}
.opt input{{accent-color:var(--accent);margin:0;flex:0 0 auto}}
.opt:has(input:checked){{border-color:var(--accent);background:var(--card)}}
.sel-out{{margin-top:10px;padding:10px 12px;border-radius:8px;background:var(--card);
  border:1px solid var(--ok-line);font-size:13.5px;color:var(--text)}}

/* tables */
.tool{{background:var(--card);border:1px solid var(--line);border-radius:13px;padding:18px 20px;
  margin-bottom:14px;box-shadow:var(--shadow)}}
.tool-head h3{{margin:0 0 3px;font-size:15px;font-weight:660}}
.tool-head p{{margin:0 0 12px;color:var(--muted);font-size:13px}}
.tbl-wrap{{overflow-x:auto;-webkit-overflow-scrolling:touch}}
table{{width:100%;border-collapse:collapse;font-size:13.5px}}
th{{text-align:left;font-weight:650;color:var(--muted);font-size:12px;letter-spacing:.02em;
  padding:7px 10px;border-bottom:1px solid var(--line);white-space:nowrap;background:transparent}}
td{{padding:9px 10px;border-bottom:1px solid var(--line);vertical-align:top}}
tr:last-child td{{border-bottom:0}}
tbody tr:hover td{{background:color-mix(in srgb,var(--accent-soft) 45%,transparent)}}
.nowrap{{white-space:nowrap}}
.tbl-foot{{margin:11px 0 0;color:var(--muted);font-size:12.5px;padding-top:9px;border-top:1px dashed var(--line)}}

/* footer */
footer{{border-top:1px solid var(--line);padding:22px 20px 40px;max-width:1180px;margin:0 auto;
  color:var(--muted);font-size:12.5px;line-height:1.8}}
footer a{{color:var(--accent);text-decoration:none}}
footer a:hover{{text-decoration:underline}}

@media (max-width:900px){{
  .layout{{grid-template-columns:1fr;gap:18px;padding-top:18px}}
  .main{{padding-left:8px}}
  .side-col{{position:static}}
  .side{{display:none;max-height:none;overflow:visible;padding:0}}
  .side.open{{display:block;margin-top:9px}}
  .side-toggle{{display:flex;align-items:center;justify-content:space-between;width:100%;
    border:1px solid var(--line);background:var(--card);color:var(--text);border-radius:9px;
    padding:9px 13px;font:600 13px/1.3 inherit;cursor:pointer;box-shadow:var(--shadow)}}
  .tg-state{{color:var(--accent);font-weight:600;font-size:12.5px}}
  .side-toggle[aria-expanded="true"] .tg-state::after{{content:"▲";font-size:9px;margin-left:3px}}
  .side-toggle[aria-expanded="false"] .tg-state::after{{content:"▼";font-size:9px;margin-left:3px}}
  .side-g{{margin-bottom:10px}}
  .side ol{{display:flex;flex-wrap:wrap;gap:5px}}
  .side a{{border-left:0;border:1px solid var(--line);padding:4px 9px;font-size:12px;
    background:var(--card);max-width:100%}}
  .side a.on{{border-color:var(--accent)}}
  .nav-txt{{max-width:132px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
  .howto{{grid-template-columns:1fr}}
  .phase-desc{{margin-left:0}}
  .step{{padding:18px 16px 16px}}
  .step-head{{row-gap:8px}}
  .step-title{{flex:1 1 100%}}
  .step-time{{margin-left:auto}}
  .step-no{{position:static;width:auto;height:auto;min-width:24px;padding:1px 7px;margin:0 0 7px;
    border-radius:5px;font-size:10px;display:inline-grid;place-items:center}}
  .bar{{display:none}}
  .jump,.reset{{padding:5px 9px;font-size:12px}}
  .hd-t p{{display:none}}
}}
@media print{{
  header,.side,.check,.reset{{display:none!important}}
  .layout{{display:block;padding:0}}
  .step,.tool{{break-inside:avoid;box-shadow:none}}
  body{{background:#fff}}
}}
</style>
</head>
<body>
<header>
  <div class="hd">
    <div class="hd-t">
      <h1>{title}</h1>
      <p>{subtitle}</p>
    </div>
    <div class="prog">
      <span class="pnum" id="pnum">0 / {total}</span>
      <div class="bar"><i id="bar"></i></div>
    </div>
    <button class="jump" id="jump" hidden>继续</button>
    <button class="reset" id="reset">重置</button>
  </div>
</header>

<div class="layout">
{body}
</div>

<footer>
  主依据：<a href="{source_url}" target="_blank" rel="noopener">{source_title}</a>　·　发布 {source_date}　·　时长 {duration}<br>
  交叉验证：{verify}<br>
  步骤按视频流程整理。{note}<br>
  本页整理于 {built}。工具名与版本上限时效性极强，动手当天请重新确认。
</footer>

<script>
(function () {{
  var KEY = 'ps5guide.v1';
  var state = {{ done: [], mirror: null, fields: {{}} }};
  try {{
    var raw = localStorage.getItem(KEY);
    if (raw) {{
      var o = JSON.parse(raw) || {{}};
      if (Array.isArray(o.done)) state.done = o.done;
      if (o.mirror) state.mirror = o.mirror;
      if (o.fields && typeof o.fields === 'object') state.fields = o.fields;
    }}
  }} catch (e) {{}}

  function save() {{
    try {{ localStorage.setItem(KEY, JSON.stringify(state)); }} catch (e) {{}}
  }}

  var steps = Array.prototype.slice.call(document.querySelectorAll('[data-step]'));
  var TOTAL = steps.length;

  function paintProgress() {{
    var n = state.done.length;
    var pnum = document.getElementById('pnum');
    var bar = document.getElementById('bar');
    if (pnum) pnum.textContent = n + ' / ' + TOTAL;
    if (bar) bar.style.width = (TOTAL ? (n / TOTAL * 100) : 0) + '%';
  }}

  function paintStep(id) {{
    var card = document.getElementById(id);
    if (!card) return;
    var btn = card.querySelector('[data-check]');
    var on = state.done.indexOf(id) >= 0;
    if (btn) {{
      btn.setAttribute('aria-pressed', on ? 'true' : 'false');
      var t = btn.querySelector('.ck-txt');
      if (t) t.textContent = on ? '已完成' : '做完了';
    }}
    card.classList.toggle('done', on);
    var nav = document.querySelector('[data-nav="' + id + '"]');
    if (nav) nav.classList.toggle('done', on);
  }}

  function paintAll() {{
    steps.forEach(function (s) {{ paintStep(s.getAttribute('data-step')); }});
    paintProgress();
  }}

  // 勾选
  document.addEventListener('click', function (ev) {{
    var btn = ev.target.closest ? ev.target.closest('[data-check]') : null;
    if (btn) {{
      var id = btn.getAttribute('data-check');
      var i = state.done.indexOf(id);
      if (i >= 0) state.done.splice(i, 1); else state.done.push(id);
      save(); paintStep(id); paintProgress(); paintJump();
      return;
    }}
    var r = ev.target.closest ? ev.target.closest('#reset') : null;
    if (r) {{
      if (confirm('清空所有勾选和填写内容？')) {{
        state = {{ done: [], mirror: null, fields: {{}} }};
        save(); paintAll(); paintJump();
        Array.prototype.forEach.call(document.querySelectorAll('.pv-input'), function (el) {{
          el.value = '';
        }});
        Array.prototype.forEach.call(document.querySelectorAll('input[name="mirror"]'), function (el) {{
          el.checked = false;
        }});
        var out = document.getElementById('mirrorOut');
        if (out) {{ out.hidden = true; out.innerHTML = ''; }}
      }}
    }}
  }});

  // 输入框持久化
  Array.prototype.forEach.call(document.querySelectorAll('.pv-input'), function (el) {{
    var f = el.getAttribute('data-field');
    if (f && state.fields[f] != null) el.value = state.fields[f];
    el.addEventListener('input', function () {{
      if (!f) return;
      state.fields[f] = el.value;
      save();
    }});
  }});

  // 镜像档位选择器
  var mapEl = document.getElementById('mirrorMap');
  var out = document.getElementById('mirrorOut');
  var radios = Array.prototype.slice.call(document.querySelectorAll('input[name="mirror"]'));
  var map = {{}};
  if (mapEl) {{ try {{ map = JSON.parse(mapEl.textContent) || {{}}; }} catch (e) {{}} }}

  function fmt(s) {{
    return String(s).replace(/\\*\\*(.+?)\\*\\*/g, '<strong>$1</strong>');
  }}
  function paintMirror() {{
    if (!out) return;
    if (!state.mirror || !map[state.mirror]) {{ out.hidden = true; out.innerHTML = ''; return; }}
    out.hidden = false;
    out.innerHTML = '<b>结论：</b>' + fmt(map[state.mirror]);
  }}
  radios.forEach(function (r) {{
    if (r.value === state.mirror) r.checked = true;
    r.addEventListener('change', function () {{
      state.mirror = r.value; save(); paintMirror();
    }});
  }});

  // 导航高亮
  var navLinks = Array.prototype.slice.call(document.querySelectorAll('[data-nav]'));
  function setActive(id) {{
    navLinks.forEach(function (a) {{
      a.classList.toggle('on', a.getAttribute('data-nav') === id);
    }});
  }}
  if ('IntersectionObserver' in window) {{
    var io = new IntersectionObserver(function (entries) {{
      entries.forEach(function (en) {{
        if (en.isIntersecting) setActive(en.target.getAttribute('data-step'));
      }});
    }}, {{ rootMargin: '-84px 0px -62% 0px', threshold: 0 }});
    steps.forEach(function (s) {{ io.observe(s); }});
  }}

  // 移动端导航折叠
  var tg = document.getElementById('sideToggle');
  var sideEl = document.getElementById('side');
  if (tg && sideEl) {{
    tg.addEventListener('click', function () {{
      var on = sideEl.classList.toggle('open');
      tg.setAttribute('aria-expanded', on ? 'true' : 'false');
      var st = tg.querySelector('.tg-state');
      if (st) st.textContent = on ? '收起' : '展开';
    }});
    navLinks.forEach(function (a) {{
      a.addEventListener('click', function () {{
        if (window.innerWidth <= 900) {{
          sideEl.classList.remove('open');
          tg.setAttribute('aria-expanded', 'false');
          var st2 = tg.querySelector('.tg-state');
          if (st2) st2.textContent = '展开';
        }}
      }});
    }});
  }}

  // 「继续」跳到第一个未完成的步骤
  var jump = document.getElementById('jump');
  function paintJump() {{
    if (!jump) return;
    var next = null;
    for (var i = 0; i < steps.length; i++) {{
      var sid = steps[i].getAttribute('data-step');
      if (state.done.indexOf(sid) < 0) {{ next = steps[i]; break; }}
    }}
    if (!next || state.done.length === 0) {{ jump.hidden = true; return; }}
    jump.hidden = false;
    var no = next.querySelector('.step-no');
    jump.textContent = '继续 · ' + (no ? no.textContent.trim() : '');
    jump.onclick = function () {{
      next.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
    }};
  }}

  paintAll();
  paintMirror();
  paintJump();
  setTimeout(function () {{
    document.documentElement.classList.add('ready');
  }}, 30);
}})();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    build()
