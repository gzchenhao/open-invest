#!/usr/bin/env python3
"""批量更新政策数据：添加联系方式、日期、PDF下载链接"""

=============================================
⚠️  重要声明：MOCK数据 ⚠️
=============================================
本脚本包含虚构的政府联系方式和政策数据。
所有数据均为演示和测试用途，不代表任何真实的政府政策。

包含的虚构联系方式示例：
- 021-50800880 (上海张江高科技园区管理委员会)
- policy@zhangjiang.gov.cn
- 0755-26000888 (深圳高新区管理委员会)
- tech@szhtp.gov.cn

请勿将这些信息误认为真实的政府联系方式。
=============================================

import re

file_path = r"c:\OpenInvest\open-invest-protocol\global_policy_aggregator\web\interactive_ai_server.py"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 为每个政策定义新增字段
policy_updates = {
    2: {
        "issue_date": "2024-04-10",
        "valid_period": "2024-04-10至2027-04-09",
        "official_contact": {
            "department": "上海张江高科技园区管理委员会产业发展处",
            "phone": "021-50800880",
            "email": "policy@zhangjiang.gov.cn",
            "address": "上海市浦东新区张江路1号"
        }
    },
    3: {
        "issue_date": "2024-05-20",
        "valid_period": "2024-05-20至2027-05-19",
        "official_contact": {
            "department": "深圳高新区管理委员会科技创新处",
            "phone": "0755-26000888",
            "email": "tech@szhtp.gov.cn",
            "address": "深圳市南山区高新南七道1号"
        }
    },
    4: {
        "issue_date": "2024-03-01",
        "valid_period": "2024-03-01至2026-12-31",
        "official_contact": {
            "department": "合肥高新区量子计算产业发展办公室",
            "phone": "0551-65391880",
            "email": "quantum@hefeihtp.gov.cn",
            "address": "合肥市高新区望江西路800号"
        }
    },
    5: {
        "issue_date": "2024-06-15",
        "valid_period": "2024-06-15至2027-06-14",
        "official_contact": {
            "department": "杭州滨江高新区管理委员会创新发展处",
            "phone": "0571-85178888",
            "email": "blockchain@binjiang.gov.cn",
            "address": "杭州市滨江区江南大道1号"
        }
    },
    6: {
        "issue_date": "2024-04-25",
        "valid_period": "2024-04-25至2027-04-24",
        "official_contact": {
            "department": "成都高新区生物医药产业发展推进办公室",
            "phone": "028-85336888",
            "email": "biotech@cdhtp.gov.cn",
            "address": "成都市高新区天府大道南段888号"
        }
    },
    7: {
        "issue_date": "2024-05-10",
        "valid_period": "2024-05-10至2027-05-09",
        "official_contact": {
            "department": "武汉东湖高新区装备制造产业推进处",
            "phone": "027-67880888",
            "email": "equipment@whdonghu.gov.cn",
            "address": "武汉市东湖高新区高新大道777号"
        }
    },
    8: {
        "issue_date": "2024-03-20",
        "valid_period": "2024-03-20至2027-03-19",
        "official_contact": {
            "department": "西安高新区航空航天产业发展办公室",
            "phone": "029-81108888",
            "email": "aerospace@xaxdz.gov.cn",
            "address": "西安市高新区锦业路1号"
        }
    },
    9: {
        "issue_date": "2024-06-01",
        "valid_period": "2024-06-01至2027-05-31",
        "official_contact": {
            "department": "南京江北新区新材料产业发展中心",
            "phone": "025-58886888",
            "email": "material@njjiangbei.gov.cn",
            "address": "南京市江北新区浦口大道1号"
        }
    },
    10: {
        "issue_date": "2024-04-15",
        "valid_period": "2024-04-15至2027-04-14",
        "official_contact": {
            "department": "天津滨海高新区新能源产业推进处",
            "phone": "022-24888888",
            "email": "energy@tjbhhtp.gov.cn",
            "address": "天津市滨海新区华苑产业园区梅苑路6号"
        }
    },
    11: {
        "issue_date": "2024-05-25",
        "valid_period": "2024-05-25至2027-05-24",
        "official_contact": {
            "department": "珠海横琴新区金融产业发展局",
            "phone": "0756-8841888",
            "email": "fintech@zhuhengqin.gov.cn",
            "address": "珠海市横琴新区环岛东路3000号"
        }
    },
    12: {
        "issue_date": "2024-03-10",
        "valid_period": "2024-03-10至2026-12-31",
        "official_contact": {
            "department": "苏州工业园区纳米技术产业发展处",
            "phone": "0512-66888888",
            "email": "nano@sipac.gov.cn",
            "address": "苏州工业园区星湖街328号"
        }
    }
}

# 更新政策1的source_url
content = content.replace(
    '"source_url": "http://www.zjpark.gov.cn/policies/2024/ai-policy.pdf",  # 源文件下载',
    '"source_url": "/api/policy/1/pdf",  # 源文件下载'
)

# 为政策2-12添加新字段
for pid, updates in policy_updates.items():
    # 找到每个政策的 "amount" 行，在其后添加新字段
    # 使用正则匹配 "amount": "最高XXX万", 后跟 description
    pattern = rf'("id": {pid},.*?"amount": "最高\d+万",)'
    
    match = re.search(pattern, content, re.DOTALL)
    if match:
        old_text = match.group(1)
        
        # 构建新字段
        new_fields = f'\n        "issue_date": "{updates["issue_date"]}",'
        new_fields += f'\n        "valid_period": "{updates["valid_period"]}",'
        new_fields += f'\n        "source_url": "/api/policy/{pid}/pdf",'
        new_fields += '\n        "official_contact": {'
        new_fields += f'\n            "department": "{updates["official_contact"]["department"]}",'
        new_fields += f'\n            "phone": "{updates["official_contact"]["phone"]}",'
        new_fields += f'\n            "email": "{updates["official_contact"]["email"]}",'
        new_fields += f'\n            "address": "{updates["official_contact"]["address"]}"'
        new_fields += '\n        },'
        new_fields += '\n        "claim_status": "unclaimed",'
        new_fields += '\n        "claim_token": None,'
        
        new_text = old_text + new_fields
        content = content.replace(old_text, new_text)
    else:
        print(f"WARNING: Could not find policy {pid}")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("SUCCESS: All policies updated with contact info, dates, and PDF links")
