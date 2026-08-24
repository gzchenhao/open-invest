"""
原始政策数据示例
提供一些原始的政策网页文本，用于演示清洗功能

⚠️ TASK-P0-2 DATA-INTEGRITY 声明：
以下文本均为 SYNTHETIC/MOCK 示例（非真实政府公文），仅用于演示 parser/cleaner 流程，
其中的机构名称、日期、金额、邮箱均不得作为真实政策信息引用或标记为 VERIFIED。
"""

# 上海张江高科技园区原始政策文本
SHANGHAI_POLICY_RAW = """
上海张江高科技园区关于支持人工智能产业发展的若干政策

发布机构：上海张江高科技园区管理委员会
发布日期：2024年1月15日
生效日期：2024年2月1日
有效期：至2025年12月31日

为深入贯彻落实国家关于加快发展新一代人工智能的战略部署，推动张江科学城人工智能产业高质量发展，特制定本政策。

一、财政支持政策

（一）研发资助
对从事人工智能基础研究、核心算法、关键技术研发的企业，给予最高1000万元的研发资助。资助金额根据企业研发投入情况、技术先进性和市场前景综合评定。

（二）设备补贴
对企业购买人工智能专用设备、高性能计算设备等，给予设备采购金额30%的补贴，单个企业年度补贴最高不超过500万元。

（三）场地补贴
在张江科学城内租用办公场地的人工智能企业，享受前三年50%的租金补贴，每年补贴最高不超过200万元。

二、税收优惠政策

（一）企业所得税优惠
符合条件的人工智能企业，享受企业所得税"三免三减半"优惠政策，即前三年免征企业所得税，后三年减半征收。

（二）研发费用加计扣除
人工智能企业的研发费用，可按175%的比例在企业所得税前加计扣除。

（三）增值税优惠
人工智能软件产品增值税超税负部分即征即退，实际税负超过3%的部分享受即征即退政策。

三、人才引进政策

（一）人才补贴
对引进的人工智能领域高端人才，给予每人50-100万元的人才补贴，分三年发放。

（二）住房保障
为引进的高端人才提供人才公寓，租金享受市场价60%的优惠。

（三）子女教育
引进人才的子女可优先安排在张江科学城内优质学校就读。

四、申请条件

（一）基本条件
1. 在张江科学城内注册的人工智能企业
2. 企业成立时间不超过5年
3. 研发投入占营业收入比例不低于15%
4. 拥有核心自主知识产权

（二）专项条件
1. 从事人工智能基础研究、核心算法、关键技术研发
2. 技术具有先进性和创新性
3. 有明确的市场应用前景
4. 团队结构合理，核心成员具有相关领域经验

五、申请流程

（一）在线申请
1. 登录张江科学城官方网站
2. 在线填写申请表单
3. 上传相关证明材料
4. 提交申请

（二）材料审核
1. 材料初审（5个工作日）
2. 专家评审（15个工作日）
3. 政府审批（10个工作日）

（三）签约落地
1. 签订投资协议
2. 享受优惠政策
3. 正式入驻园区

六、联系方式

联系人：张经理
联系电话：021-12345678
电子邮箱：zhang@zjpark.gov.cn
办公地址：上海市浦东新区张江高科技园区招商局

七、附则

1. 本政策由上海张江高科技园区管理委员会负责解释
2. 本政策自发布之日起施行
3. 如有疑问，请咨询相关部门

上海张江高科技园区管理委员会
2024年1月15日
"""

# 硅谷科技创新中心原始政策文本
SILICON_VALLEY_POLICY_RAW = """
Silicon Valley Innovation Hub - AI Startup Program 2024

Program Overview:
The Silicon Valley Innovation Hub is launching its AI Startup Program 2024 to support innovative AI companies and accelerate the development of artificial intelligence technologies.

Financial Incentives:
- Seed Funding: Up to $200,000 for early-stage AI startups
- Office Space: 50% discount on office rental for 2 years
- Tax Credits: California R&D Tax Credit up to $1,000,000
- Cloud Credits: $50,000 worth of AWS/Azure cloud services

Eligibility Requirements:
- AI/ML focused technology company
- Must have Series A+ funding
- Diverse team composition (40%+ underrepresented groups)
- Innovative AI technology with market potential

Application Process:
1. Online Application Submission
   - Complete the online application form
   - Submit business plan and team bios
   - Provide technology description

2. Due Diligence Review
   - Financial statement verification
   - IP portfolio assessment
   - Market analysis evaluation

3. Investment Committee Approval
   - Technical review
   - Business model assessment
   - Team evaluation

4. Program Agreement
   - Sign program agreement
   - Receive funding and benefits
   - Join innovation hub

Contact Information:
Program Manager: Sarah Johnson
Email: sarah@svhub.org
Phone: +1-650-555-0123
Address: 350 Tasman Drive, Palo Alto, CA

Program Duration: 2 years
Application Deadline: December 31, 2024
"""

# 欧盟数字计划原始政策文本
EU_DIGITAL_POLICY_RAW = """
EU Digital Innovation Program 2024

Program Description:
The European Commission's Digital Innovation Program supports digital transformation and innovation across European member states. The program aims to accelerate the adoption of digital technologies and foster cross-border collaboration.

Financial Support:
- R&D Funding: Up to €750,000 for digital innovation projects
- Office Space: 40% subsidy on office rental for 3 years
- Tax Incentives: 20% corporate tax reduction for 4 years
- Talent Grants: Up to €250,000 for digital talent recruitment

Eligibility Criteria:
- Company must be registered in an EU member state
- Digital transformation project required
- Cross-border collaboration mandatory (minimum 3 countries)
- Open source contribution expected

Application Process:
1. Pre-application Consultation
   - Contact program advisors
   - Discuss project ideas
   - Receive guidance on requirements

2. Full Application Submission
   - Complete application package
   - Submit detailed project proposal
   - Provide financial projections

3. Expert Evaluation
   - Technical assessment
   - Impact evaluation
   - Feasibility analysis

4. Final Approval
   - Commission review
   - Funding decision
   - Agreement signing

Contact Information:
Program Coordinator: Dr. Maria Schmidt
Email: maria.schmidt@ec.europa.eu
Phone: +32-2-500-1234
Address: B-1049 Brussels, Belgium

Program Period: January 2024 - February 2027
"""

# 深圳南山科技园原始政策文本
SHENZHEN_POLICY_RAW = """
深圳市南山区关于支持生物医药产业发展的若干措施

发布机构：深圳市南山区人民政府
发布日期：2024年2月1日
生效日期：2024年3月1日
有效期：至2026年2月28日

为加快南山区生物医药产业发展，培育新的经济增长点，特制定本措施。

一、资金支持

（一）新药研发资助
对开展新药研发的企业，给予最高800万元的研发资助。资助金额根据研发阶段、技术难度和市场前景确定。

（二）临床试验补贴
企业开展临床试验的，给予临床试验费用30%的补贴，单个企业年度补贴最高不超过500万元。

（三）GMP认证补贴
企业通过GMP认证的，给予认证费用50%的补贴，最高不超过200万元。

二、税收优惠

（一）企业所得税优惠
符合条件的高新技术企业，享受15%的企业所得税优惠税率。

（二）研发费用加计扣除
企业的研发费用，可按175%的比例在企业所得税前加计扣除。

（三）房产税优惠
企业自用的房产、土地，免征房产税和城镇土地使用税。

三、场地支持

（一）办公场地
在南山区生物医药产业园内租用办公场地，享受前两年免租金，后两年租金50%的优惠。

（二）实验室场地
租用实验室场地的，给予实验室改造费用30%的补贴，最高不超过300万元。

四、人才政策

（一）人才补贴
引进的生物医药领域高端人才，给予每人100-200万元的人才补贴。

（二）住房保障
为引进的高端人才提供人才住房，租金享受市场价50%的优惠。

（三）子女教育
引进人才的子女可优先安排在南山区内优质学校就读。

五、申请条件

（一）基本条件
1. 在南山区注册的生物医药企业
2. 企业成立时间不超过8年
3. 研发投入占营业收入比例不低于10%
4. 拥有自主知识产权

（二）专项条件
1. 从事新药研发、医疗器械研发等
2. 技术具有先进性和创新性
3. 有明确的市场前景
4. 团队具有相关领域经验

六、申请流程

（一）在线申请
1. 登录南山区科技创新服务平台
2. 在线填写申请表单
3. 上传相关证明材料
4. 提交申请

（二）审核审批
1. 材料初审（7个工作日）
2. 专家评审（20个工作日）
3. 政府审批（15个工作日）

（三）签约落地
1. 签订合作协议
2. 享受优惠政策
3. 入驻产业园区

七、联系方式

联系人：李经理
联系电话：0755-12345678
电子邮箱：li@nsz.gov.cn
办公地址：深圳市南山区科技创新中心

八、附则

1. 本措施由南山区科技创新局负责解释
2. 本措施自发布之日起施行
3. 如有疑问，请咨询相关部门

深圳市南山区人民政府
2024年2月1日
"""

# 杭州滨江高新区原始政策文本
HANGZHOU_POLICY_RAW = """
杭州滨江高新区关于支持数字经济产业发展的政策意见

发布机构：杭州滨江高新技术产业开发区管理委员会
发布日期：2024年1月20日
生效日期：2024年2月20日
有效期：至2025年12月31日

为加快滨江高新区数字经济发展，培育数字经济新动能，特制定本政策意见。

一、财政支持

（一）重大项目资助
对投资额超过1亿元的数字经济重大项目，给予最高2000万元的资助。

（二）平台建设补贴
建设数字经济公共服务平台的，给予平台建设费用50%的补贴，最高不超过500万元。

（三）应用推广补贴
企业开展数字化应用推广的，给予推广费用30%的补贴，最高不超过300万元。

二、税收优惠

（一）企业所得税优惠
符合条件的高新技术企业，享受15%的企业所得税优惠税率。

（二）研发费用加计扣除
企业的研发费用，可按175%的比例在企业所得税前加计扣除。

（三）增值税优惠
软件产品增值税超税负部分即征即退。

三、人才政策

（一）人才补贴
引进的数字经济领域高端人才，给予每人50-150万元的人才补贴。

（二）住房保障
为引进的高端人才提供人才公寓，租金享受市场价60%的优惠。

（三）创业支持
高层次人才在滨江区创业的，给予最高500万元的创业资助。

四、申请条件

（一）基本条件
1. 在滨江高新区注册的数字经济企业
2. 企业成立时间不超过6年
3. 研发投入占营业收入比例不低于12%
4. 具有自主知识产权

（二）专项条件
1. 从事云计算、大数据、人工智能等数字经济领域
2. 技术具有创新性和先进性
3. 有明确的市场应用前景
4. 团队结构合理

五、申请流程

（一）在线申请
1. 登录滨江高新区政务服务网
2. 在线填写申请表单
3. 上传相关证明材料
4. 提交申请

（二）审核审批
1. 材料初审（5个工作日）
2. 专家评审（15个工作日）
3. 政府审批（10个工作日）

（三）公示公告
1. 在政府网站公示
2. 接受社会监督
3. 发布最终结果

六、联系方式

联系人：王经理
联系电话：0571-12345678
电子邮箱：wang@binjiang.gov.cn
办公地址：杭州市滨江区网商路599号

七、附则

1. 本政策意见由滨江高新区管委会负责解释
2. 本政策意见自发布之日起施行
3. 如有疑问，请咨询相关部门

杭州滨江高新技术产业开发区管理委员会
2024年1月20日
"""

# 原始政策数据列表
RAW_POLICIES = [
    {
        "id": "shanghai-ai-2024",
        "name": "上海张江人工智能政策",
        "jurisdiction": "上海",
        "raw_text": SHANGHAI_POLICY_RAW,
        "source": "上海张江高科技园区"
    },
    {
        "id": "silicon-valley-ai-2024",
        "name": "硅谷AI创业计划",
        "jurisdiction": "California",
        "raw_text": SILICON_VALLEY_POLICY_RAW,
        "source": "Silicon Valley Innovation Hub"
    },
    {
        "id": "eu-digital-2024",
        "name": "欧盟数字创新计划",
        "jurisdiction": "EU",
        "raw_text": EU_DIGITAL_POLICY_RAW,
        "source": "European Commission"
    },
    {
        "id": "shenzhen-biotech-2024",
        "name": "深圳南山生物医药政策",
        "jurisdiction": "深圳",
        "raw_text": SHENZHEN_POLICY_RAW,
        "source": "深圳市南山区政府"
    },
    {
        "id": "hangzhou-digital-2024",
        "name": "杭州滨江数字经济政策",
        "jurisdiction": "杭州",
        "raw_text": HANGZHOU_POLICY_RAW,
        "source": "杭州滨江高新区"
    }
]

if __name__ == "__main__":
    # 打印原始政策数据示例
    for policy in RAW_POLICIES:
        print(f"Policy ID: {policy['id']}")
        print(f"Name: {policy['name']}")
        print(f"Jurisdiction: {policy['jurisdiction']}")
        print(f"Source: {policy['source']}")
        print(f"Length: {len(policy['raw_text'])} characters")
        print("-" * 50)