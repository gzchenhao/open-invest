#!/usr/bin/env python3
"""
TASK-P0-2：对 interactive_ai_server.py 内嵌的 12 条演示政策执行数据治理：
1. 每条政策追加 is_mock=True / verification_status="mock"
2. official_contact 的 phone/email/address（AI 生成的不可验证联系方式）置 None，
   追加 contact_status="unverified"（第二十二条：没有联系方式比错误联系方式安全一万倍）
3. 前端 JS 联系方式渲染改为空值安全（显示"未核验"）
4. 页面头部与 PDF 增加"演示数据"显著声明
只做标记与置 null，不删除任何政策记录。
"""
import re
from pathlib import Path

path = Path(__file__).resolve().parent.parent / "web" / "interactive_ai_server.py"
text = path.read_text(encoding="utf-8")
original = text

# ---- 1. 每条政策追加 mock 标记 ----
text, n_id = re.subn(
    r'(\{\s*\n\s*"id": \d+,)',
    r'\1\n        "is_mock": True,  # TASK-P0-2: 演示数据显式标记（非真实政府政策）\n        "verification_status": "mock",',
    text)
assert n_id == 12, f"expected 12 policies, got {n_id}"

# ---- 2. 虚构联系方式置 None ----
text, n_phone = re.subn(
    r'"phone": "[^"]*",',
    '"phone": None,  # TASK-P0-2: 未经官方来源核验的电话一律置 null',
    text)
assert n_phone == 12, f"expected 12 phones, got {n_phone}"

text, n_email = re.subn(
    r'"email": "[^"]*",\n',
    '"email": None,  # TASK-P0-2: 未经官方来源核验的邮箱一律置 null\n',
    text)
assert n_email == 12, f"expected 12 emails, got {n_email}"

text, n_addr = re.subn(
    r'"address": "[^"]*"\n(\s*)\}',
    '"address": None,  # TASK-P0-2: 未经官方来源核验的地址一律置 null\n            "contact_status": "unverified"  # 联系方式未核验（DATA-INTEGRITY-003）\n\\1}',
    text)
assert n_addr == 12, f"expected 12 addresses, got {n_addr}"

# ---- 3. 数据头注释明确 MOCK ----
text = text.replace(
    "# 模拟政策数据（增强版 - 包含完整信息）",
    "# 演示政策数据（MOCK）：is_mock=True 显式标记；联系方式/来源均未经官方核验。\n"
    "# 依据 TASK-P0-2 DATA-INTEGRITY 规则：宁可 null，不要猜。")

# ---- 4. 前端联系方式渲染：空值安全 + 未核验提示 ----
text = text.replace(
    "<h4 style=\"color: #1976d2; margin-bottom: 8px;\">📞 官方联系方式</h4>",
    "<h4 style=\"color: #1976d2; margin-bottom: 8px;\">📞 官方联系方式（未核验）</h4>")
text = text.replace(
    "<p style=\"margin: 5px 0; color: #555;\"><strong>部门：</strong>${policy.official_contact.department}</p>",
    "<p style=\"margin: 5px 0; color: #555;\"><strong>部门：</strong>${policy.official_contact.department || '未核验'}</p>")
text = text.replace(
    "<p style=\"margin: 5px 0; color: #555;\"><strong>电话：</strong>${policy.official_contact.phone}</p>",
    "<p style=\"margin: 5px 0; color: #555;\"><strong>电话：</strong>${policy.official_contact.phone || '未核验（待官方认领后提供）'}</p>")
text = text.replace(
    "<p style=\"margin: 5px 0; color: #555;\"><strong>邮箱：</strong>${policy.official_contact.email}</p>",
    "<p style=\"margin: 5px 0; color: #555;\"><strong>邮箱：</strong>${policy.official_contact.email || '未核验（待官方认领后提供）'}</p>")
text = text.replace(
    "<p style=\"margin: 5px 0; color: #555;\"><strong>地址：</strong>${policy.official_contact.address}</p>",
    "<p style=\"margin: 5px 0; color: #555;\"><strong>地址：</strong>${policy.official_contact.address || '未核验'}</p>")

# ---- 5. 页面头部增加演示数据声明横幅 ----
text = text.replace(
    '''<h1>🚀 OpenInvest AI政策查询系统</h1>
            <p>智能发现 · 精准匹配 · 高效申请</p>
        </div>''',
    '''<h1>🚀 OpenInvest AI政策查询系统</h1>
            <p>智能发现 · 精准匹配 · 高效申请</p>
            <p style="margin-top: 12px; padding: 10px 16px; background: #fff3cd; color: #856404; border: 1px solid #ffeeba; border-radius: 8px; font-size: 0.9em;">
                ⚠️ 数据声明：当前展示的政策均为 <strong>MOCK 演示数据</strong>（is_mock=true），
                未经官方来源核验，不得作为申报、投资或决策依据。联系方式未经核验前一律留空。
            </p>
        </div>''')

# ---- 6. PDF：联系方式空值安全 + 演示数据声明 ----
text = text.replace(
    '''    pdf.cell(0, 7, f"  部门: {contact.get('department', '')}", ln=True)
        pdf.cell(0, 7, f"  电话: {contact.get('phone', '')}", ln=True)
        pdf.cell(0, 7, f"  邮箱: {contact.get('email', '')}", ln=True)
        pdf.cell(0, 7, f"  地址: {contact.get('address', '')}", ln=True)''',
    '''    pdf.cell(0, 7, f"  部门: {contact.get('department') or '未核验'}", ln=True)
        pdf.cell(0, 7, f"  电话: {contact.get('phone') or '未核验（待官方认领后提供）'}", ln=True)
        pdf.cell(0, 7, f"  邮箱: {contact.get('email') or '未核验（待官方认领后提供）'}", ln=True)
        pdf.cell(0, 7, f"  地址: {contact.get('address') or '未核验'}", ln=True)''')
text = text.replace(
    '''    pdf.cell(0, 7, f"本文档由OpenInvest平台自动生成 | 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True, align="C")''',
    '''    pdf.cell(0, 7, "声明：本政策为 MOCK 演示数据（is_mock=true），未经官方来源核验，仅供参考", ln=True, align="C")
    pdf.cell(0, 7, f"本文档由OpenInvest平台自动生成 | 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True, align="C")''')

assert text != original, "no changes applied"
path.write_text(text, encoding="utf-8")
print(f"[OK] interactive_ai_server.py governed: id={n_id} phone={n_phone} email={n_email} addr={n_addr}")
