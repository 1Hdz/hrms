# -*- coding: utf-8 -*-
"""T3：预置制度知识库条目（可重复运行，不会产生重复数据）。
运行：python init_knowledge.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ems.settings")

import django
django.setup()

from app01.models import Knowledge

DATA = [
    ("考勤制度", "公司标准工作时间为周一至周五 9:00 至 18:00，午休 1 小时。员工须每日上下班各打卡一次。"
                 "迟到或早退 30 分钟以内记为迟到，超过 30 分钟记为缺勤半天；当月累计迟到 3 次取消当月全勤奖。"
                 "因公外出需提前在系统报备。"),
    ("请假制度", "员工请假须在系统提交申请并经直属主管审批。年假按工龄计算：入职满 1 年享 5 天，满 10 年享 10 天。"
                 "病假须提供医院证明，按基本工资的 80% 发放；事假为无薪假。紧急情况可先电话请假，事后 1 个工作日内补办手续。"),
    ("报销制度", "差旅费、业务招待费等可凭合规发票报销。员工在系统填写报销单并附发票，经部门负责人和财务审批后，于次月 15 日前打款。"
                 "发票抬头须为公司全称，无发票或发票不合规不予报销，报销须在费用发生后 3 个月内申请。"),
    ("加班与调休制度", "公司鼓励高效工作，确需加班须提前申请并经主管批准。工作日加班按 1.5 倍工资计算，"
                       "休息日加班可安排等时调休或按 2 倍工资计算，法定节假日加班按 3 倍工资计算。调休须在 3 个月内休完。"),
    ("薪资制度", "公司每月 10 日发放上月工资，遇节假日顺延。薪资由基本工资、岗位工资、绩效奖金和各类补贴构成，"
                 "依法代扣个人所得税及社会保险、公积金。员工对薪资负有保密义务，不得相互打探或泄露。"),
    ("试用期制度", "新员工试用期一般为 1 至 6 个月，依合同期限确定。试用期工资不低于转正工资的 80%。"
                   "试用期内依法提前 3 日通知可解除劳动合同，转正考核通过后办理转正手续。"),
]

for title, content in DATA:
    _, created = Knowledge.objects.update_or_create(
        title=title, defaults={"content": content})
    print("新增" if created else "更新", title)

print("制度条目就绪，共", Knowledge.objects.count(), "条")
