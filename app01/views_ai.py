# -*- coding: utf-8 -*-
"""AI 智能助手视图（独立文件，全新增，不改动现有 views.py）

对应任务书必做：
- T2 智能生成招聘 JD（gen_jd）
- T3 制度知识库问答（knowledge_qa）
- T4 数据智能点评（data_comment）
T1 的统一调用封装见 app01/utils/ai.py 的 LLMClient。
"""
import json

from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render

from app01.models import Attendance, Knowledge, Salary, UserInfo
from app01.utils import ai
from app01.utils.auth import login_required

# 大模型单例
client = ai.get_client()


# ============ 三段式提示词（角色 + 要求 + 输出格式）============

def jd_prompt(job_title):
    return f"""【角色】你是一名资深 HR 招聘专家，擅长撰写清晰、专业的岗位招聘说明书。
【要求】请为“{job_title}”岗位撰写一份招聘 JD，内容贴合该岗位实际工作，语言简洁专业，分点陈述。
【输出格式】严格按下面三个小标题输出，不要添加额外内容：
一、岗位职责（列出 4-6 条）
二、任职要求（列出 4-6 条，含学历、经验、技能）
三、薪资范围（给出月薪区间并简要说明福利）"""


def qa_prompt(question, docs):
    material = "\n\n".join(f"《{d.title}》：{d.content}" for d in docs)
    return f"""【角色】你是公司制度问答助手，只能依据提供的制度资料回答员工问题。
【要求】根据下面的制度资料回答员工提问，答案准确、简洁，不得编造资料以外的内容。
【输出格式】直接分点给出回答；若资料中没有相关信息，只回答“不知道”。

制度资料：
{material}

员工问题：{question}"""


def comment_prompt(user, month, attend_qs, salary, is_super):
    status_map = dict(Attendance.status_choices)
    att_lines = [f"{a.att_date}：{status_map.get(a.status)}" for a in attend_qs]
    att_text = "\n".join(att_lines) if att_lines else "该月暂无考勤记录"

    if salary and is_super:  # 超管可见金额；部门管理员脱敏
        sal_text = (f"基本工资{salary.base}，绩效{salary.performance}，补贴{salary.allowance}，"
                    f"扣款{salary.deduction}，实发{salary.actual}")
    elif salary:
        sal_text = "该月薪资已正常发放（具体金额按权限保密）"
    else:
        sal_text = "该月暂无薪资记录"

    depart = user.depart.title if user.depart else "未分配部门"
    return f"""【角色】你是企业人力资源顾问，擅长依据员工真实考勤与薪资数据给出中肯点评。
【要求】根据下面的真实数据，对该员工{month}的表现给出一句点评和一条改进建议，语气客观、鼓励。
【输出格式】分“数据点评”和“改进建议”两部分，不要罗列原始数据。

员工：{user.name}（{depart}）
考勤记录：
{att_text}

薪资数据：{sal_text}"""


# ============ T3：知识库关键词检索 ============

# 制度领域关键词，用于从中文问题中提取检索词
KEYWORDS = ["考勤", "迟到", "早退", "缺勤", "打卡", "全勤", "请假", "年假", "病假", "事假",
            "报销", "发票", "加班", "调休", "工资", "薪资", "发薪", "试用期", "转正"]


def search_knowledge(question):
    hit_words = [w for w in KEYWORDS if w in question]
    if not hit_words:
        return []
    query = Q()
    for word in hit_words:
        query |= Q(title__icontains=word) | Q(content__icontains=word)
    return list(Knowledge.objects.filter(query).distinct())


# ============ 页面与接口 ============

@login_required
def ai_workbench(request):
    """渲染 AI 工作台；员工列表经 DeptScopeManager 自动按部门过滤"""
    users = UserInfo.objects.all()
    return render(request, "ai_workbench.html", {"users": users})


def _read_post(request):
    """解析 POST JSON，返回 (data, error_response)"""
    try:
        return json.loads(request.body.decode("utf-8")), None
    except Exception:
        return None, JsonResponse({"status": False, "error": "请求数据格式错误"}, status=400)


@login_required
def gen_jd(request):
    """T2：输入岗位名称，返回结构化招聘 JD"""
    if request.method != "POST":
        return JsonResponse({"status": False, "error": "仅支持 POST"}, status=405)
    data, err = _read_post(request)
    if err:
        return err
    job_title = (data.get("job_title") or "").strip()
    if not job_title:
        return JsonResponse({"status": False, "error": "岗位名称不能为空"}, status=400)
    if len(job_title) > 50:
        return JsonResponse({"status": False, "error": "岗位名称过长"}, status=400)

    answer = client.chat(jd_prompt(job_title))
    return JsonResponse({"status": True, "answer": answer})


@login_required
def knowledge_qa(request):
    """T3：制度知识库问答；检索不到资料时直接回答“不知道”"""
    if request.method != "POST":
        return JsonResponse({"status": False, "error": "仅支持 POST"}, status=405)
    data, err = _read_post(request)
    if err:
        return err
    question = (data.get("question") or "").strip()
    if not question:
        return JsonResponse({"status": False, "error": "问题不能为空"}, status=400)
    if len(question) > 200:
        return JsonResponse({"status": False, "error": "问题过长"}, status=400)

    docs = search_knowledge(question)
    if not docs:  # 资料中没有：硬性要求回答“不知道”
        return JsonResponse({"status": True, "answer": "不知道", "matched": 0})
    answer = client.chat(qa_prompt(question, docs))
    return JsonResponse({"status": True, "answer": answer, "matched": len(docs)})


@login_required
def data_comment(request):
    """T4：针对某员工某月数据，输出点评与改进建议"""
    if request.method != "POST":
        return JsonResponse({"status": False, "error": "仅支持 POST"}, status=405)
    data, err = _read_post(request)
    if err:
        return err
    user_id = data.get("user_id")
    month = (data.get("month") or "").strip()
    if not user_id or not month:
        return JsonResponse({"status": False, "error": "请选择员工和月份"}, status=400)

    try:
        year, mon = month.split("-")
        year, mon = int(year), int(mon)
    except Exception:
        return JsonResponse({"status": False, "error": "月份格式应为 YYYY-MM"}, status=400)

    user = UserInfo.objects.filter(id=user_id).first()  # 自动部门隔离
    if not user:
        return JsonResponse({"status": False, "error": "员工不存在或无权访问"}, status=404)

    attend_qs = Attendance.objects.filter(
        user=user, att_date__year=year, att_date__month=mon)
    salary = Salary.objects.filter(user=user, month=month).first()
    is_super = "super_admin" in request.session.get("info", {}).get("role_codes", [])

    answer = client.chat(comment_prompt(user, month, attend_qs, salary, is_super))
    return JsonResponse({"status": True, "answer": answer})
