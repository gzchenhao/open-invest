#!/usr/bin/env python3
"""
TASK-P0-2.1 治理脚本：为 web/templates/ 下全部 HTML 模板与 simple_server.py
注入强制 MOCK 警示横幅（页面顶部、立即可见、不依赖交互）。

原则：只插入警示，不删除任何内容（INV-000）。
幂等：检测到已有横幅标记则跳过。
"""
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
MARKER = "P0-2.1-MOCK-DISCLOSURE"

BANNER = f'''
<!-- {MARKER}: 强制 MOCK 数据披露横幅（TASK-P0-2.1） -->
<div style="position:relative;z-index:9999;margin:0;padding:14px 20px;background:#fff3cd;color:#856404;border-bottom:3px solid #ffc107;font-size:14px;line-height:1.7;font-family:sans-serif;">
  <strong>\u26a0\ufe0f \u6f14\u793a\u6570\u636e\u58f0\u660e\uff1a</strong>
  \u5f53\u524d\u9875\u9762\u5c55\u793a\u7684\u653f\u7b56\u4fe1\u606f\u5747\u4e3a <strong>MOCK / \u6f14\u793a\u6570\u636e</strong>\uff0c\u5c1a\u672a\u7ecf\u8fc7\u5b98\u65b9\u6765\u6e90\u6838\u9a8c\uff0c
  \u4e0d\u4ee3\u8868\u4efb\u4f55\u653f\u5e9c\u90e8\u95e8\u7684\u6b63\u5f0f\u653f\u7b56\u3001\u8865\u8d34\u627f\u8bfa\u6216\u62db\u5546\u6761\u4ef6\u3002\u8bf7\u52ff\u5c06\u5176\u7528\u4e8e\u5b9e\u9645\u7533\u62a5\u3001\u6295\u8d44\u6216\u5546\u4e1a\u51b3\u7b56\u3002<br>
  <strong>\u26a0\ufe0f DEMONSTRATION DATA:</strong>
  All policy information displayed on this portal is MOCK / synthetic demonstration data and has not been
  verified against authoritative government sources. It does not represent official government policy,
  subsidy commitments, investment terms, or eligibility conditions.
</div>
'''

def inject(html: str) -> tuple:
    """在 <body...> 之后注入横幅；返回 (新内容, 是否注入)"""
    if MARKER in html:
        return html, False
    m = re.search(r"<body[^>]*>", html, re.IGNORECASE)
    if not m:
        return html, False
    pos = m.end()
    return html[:pos] + BANNER + html[pos:], True

count = 0
for f in sorted((BASE / "web" / "templates").glob("*.html")):
    text = f.read_text(encoding="utf-8")
    new, changed = inject(text)
    if changed:
        f.write_text(new, encoding="utf-8")
        count += 1
        print(f"[OK] banner injected: {f.name}")
    else:
        print(f"[SKIP] already has banner or no <body>: {f.name}")

# simple_server.py 的内联 HTML（无模板文件）
ss = BASE / "web" / "simple_server.py"
text = ss.read_text(encoding="utf-8")
if MARKER not in text:
    # 内联 HTML 字符串中的 <body> 后注入（Python 字符串内的 body 标签）
    new, changed = inject(text)
    if changed:
        ss.write_text(new, encoding="utf-8")
        count += 1
        print("[OK] banner injected: web/simple_server.py (inline HTML)")
    else:
        print("[WARN] no <body> found in simple_server.py")
else:
    print("[SKIP] simple_server.py already has banner")

print(f"DONE: {count} surfaces governed")
