from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.hashers import check_password
from django.db.models import Sum
from io import BytesIO
from app01 import models
from app01.forms import UserModelForm, PrettyModelForm, PrettyEditModelForm, LoginForm
from app01.utils.pagination import Pagination
from app01.utils.auth import login_required, permission_required
from app01.utils.code import check_code


# ============ 登录 / 退出 ============
def login(request):
    """登录页：用户名 + 密码 + 图片验证码"""
    if request.method == 'GET':
        form = LoginForm()
        return render(request, 'login.html', {'form': form})

    form = LoginForm(data=request.POST)
    if form.is_valid():
        # 先校验图片验证码
        input_code = form.cleaned_data['code']
        session_code = request.session.get('image_code', '')
        if input_code != session_code.upper():
            form.add_error('code', '验证码错误')
        else:
            # 再校验用户名密码（check_password 自动比对安全哈希）
            username = form.cleaned_data['username']
            admin = models.Admin.objects.filter(username=username).first()
            if admin and check_password(form.cleaned_data['password'], admin.password):
                role_codes = list(admin.roles.values_list('code', flat=True))
                perm_codes = list(
                    models.Permission.objects
                    .filter(role__in=admin.roles.all())
                    .values_list('code', flat=True).distinct()
                )
                request.session['info'] = {
                    'id': admin.id,
                    'username': admin.username,
                    'role_codes': role_codes,
                    'perm_codes': perm_codes,
                }
                request.session.pop('image_code', None)  # 登录成功清掉验证码
                return redirect('/depart/list/')
            form.add_error('password', '用户名或密码错误')

    return render(request, 'login.html', {'form': form})


def image_code(request):
    """生成图片验证码：图片返回给浏览器，正确答案存 session"""
    img, code_string = check_code()
    request.session['image_code'] = code_string  # 存正确答案

    stream = BytesIO()
    img.save(stream, 'png')
    return HttpResponse(stream.getvalue(), content_type='image/png')


def logout(request):
    """退出登录：清空 session"""
    request.session.flush()
    return redirect('/login/')


# ============ 部门管理 ============
@login_required
def depart_list(request):
    queryset = models.Department.objects.all()
    return render(request, 'depart_list.html', {'queryset': queryset})


@permission_required('depart_add')
def depart_add(request):
    if request.method == 'GET':
        return render(request, 'depart_add.html')
    title = request.POST.get('title')
    models.Department.objects.create(title=title)
    return redirect('/depart/list/')


@permission_required('depart_delete')
def depart_delete(request, aid):
    models.Department.objects.filter(id=aid).delete()
    return redirect('/depart/list/')


@permission_required('depart_edit')
def depart_edit(request, aid):
    row = models.Department.objects.filter(id=aid).first()
    if request.method == 'GET':
        return render(request, 'depart_edit.html', {'row': row})
    title = request.POST.get('title')
    models.Department.objects.filter(id=aid).update(title=title)
    return redirect('/depart/list/')


# ============ 用户管理 ============
@login_required
def user_list(request):
    q = request.GET.get('q', '')
    depart_id = request.GET.get('depart', '')
    queryset = models.UserInfo.objects.all()
    if q:
        queryset = queryset.filter(name__contains=q)
    if depart_id:
        queryset = queryset.filter(depart_id=depart_id)

    total_count = queryset.count()
    page = Pagination(request, total_count)
    queryset = queryset[page.start_index:page.end_index]

    return render(request, 'user_list.html', {
        'queryset': queryset,
        'q': q,
        'depart_id': int(depart_id) if depart_id else 0,
        'depart_list': models.Department.objects.all(),
        'page_html': page.html(),
    })


@login_required
def user_add(request):
    """原生表单方式（user_add.html）"""
    if request.method == 'GET':
        gender_choices = models.UserInfo.gender_choices
        depart_list = models.Department.objects.all()
        return render(request, 'user_add.html', {'gender_choices': gender_choices, 'depart_list': depart_list})
    name = request.POST.get('user')
    password = request.POST.get('pwd')
    age = request.POST.get('age')
    account = request.POST.get('ac')
    create_time = request.POST.get('ctime')
    gender = request.POST.get('gd')
    depart_id = request.POST.get('dp')
    models.UserInfo.objects.create(
        name=name,
        password=password,
        age=age,
        account=account,
        create_time=create_time,
        gender=gender,
        depart_id=depart_id,
    )
    return redirect('/user/list/')


@permission_required('user_add')
def user_model_form_add(request):
    """ModelForm方式（user_model_form_add.html）"""
    if request.method == 'GET':
        form = UserModelForm()
        return render(request, 'user_model_form_add.html', {'form': form})
    form = UserModelForm(data=request.POST, files=request.FILES)
    if form.is_valid():
        form.save()
        return redirect('/user/list/')
    return render(request, 'user_model_form_add.html', {'form': form})


@permission_required('user_edit')
def user_edit(request, uid):
    row = models.UserInfo.objects.filter(id=uid).first()
    if request.method == 'GET':
        form = UserModelForm(instance=row)
        return render(request, 'user_edit.html', {'form': form})
    form = UserModelForm(data=request.POST, files=request.FILES, instance=row)
    if form.is_valid():
        form.save()
        return redirect('/user/list/')
    return render(request, 'user_edit.html', {'form': form})


@permission_required('user_delete')
def user_delete(request, uid):
    models.UserInfo.objects.filter(id=uid).delete()
    return redirect('/user/list/')


# ============ 靓号管理 ============
@login_required
def pretty_list(request):
    q = request.GET.get('q', '')
    queryset = models.PrettyNum.objects.all().order_by('-level')
    if q:
        queryset = queryset.filter(mobile__contains=q)

    # 分页
    total_count = queryset.count()
    page = Pagination(request, total_count)
    queryset = queryset[page.start_index:page.end_index]

    return render(request, 'pretty_list.html', {'queryset': queryset, 'q': q, 'page_html': page.html()})


@permission_required('pretty_add')
def pretty_add(request):
    if request.method == 'GET':
        form = PrettyModelForm()
        return render(request, 'pretty_add.html', {'form': form})
    form = PrettyModelForm(data=request.POST)
    if form.is_valid():
        form.save()
        return redirect('/pretty/list/')
    return render(request, 'pretty_add.html', {'form': form})


@permission_required('pretty_edit')
def pretty_edit(request, pid):
    row = models.PrettyNum.objects.filter(id=pid).first()
    if request.method == 'GET':
        form = PrettyEditModelForm(instance=row)
        return render(request, 'pretty_edit.html', {'form': form})
    form = PrettyEditModelForm(data=request.POST, instance=row)
    if form.is_valid():
        form.save()
        return redirect('/pretty/list/')
    return render(request, 'pretty_edit.html', {'form': form})


@permission_required('pretty_delete')
def pretty_delete(request, pid):
    models.PrettyNum.objects.filter(id=pid).delete()
    return redirect('/pretty/list/')


# ============ 管理员管理 ============
from app01.forms import (AdminModelForm, AdminEditModelForm, AdminResetModelForm,
                        RoleModelForm, PermissionModelForm, AdminRoleModelForm,
                        AttendanceModelForm, SalaryModelForm, AnnouncementModelForm,
                        TaskModelForm)


@permission_required('admin_view')
def admin_list(request):
    """管理员列表（搜索 + 分页）"""
    q = request.GET.get('q', '')
    queryset = models.Admin.objects.all()
    if q:
        queryset = queryset.filter(username__contains=q)

    total_count = queryset.count()
    page = Pagination(request, total_count)
    queryset = queryset[page.start_index:page.end_index]

    return render(request, 'admin_list.html',
                  {'queryset': queryset, 'q': q, 'page_html': page.html()})


@permission_required('admin_add')
def admin_add(request):
    """新建管理员"""
    if request.method == 'GET':
        form = AdminModelForm()
        return render(request, 'admin_change.html', {'form': form, 'title': '新建管理员'})
    form = AdminModelForm(data=request.POST)
    if form.is_valid():
        form.save()
        return redirect('/admin/list/')
    return render(request, 'admin_change.html', {'form': form, 'title': '新建管理员'})


@permission_required('admin_edit')
def admin_edit(request, aid):
    """编辑管理员（改用户名）"""
    row = models.Admin.objects.filter(id=aid).first()
    if request.method == 'GET':
        form = AdminEditModelForm(instance=row)
        return render(request, 'admin_change.html', {'form': form, 'title': '编辑管理员'})
    form = AdminEditModelForm(data=request.POST, instance=row)
    if form.is_valid():
        form.save()
        return redirect('/admin/list/')
    return render(request, 'admin_change.html', {'form': form, 'title': '编辑管理员'})


@permission_required('admin_reset')
def admin_reset(request, aid):
    """重置密码"""
    row = models.Admin.objects.filter(id=aid).first()
    if request.method == 'GET':
        form = AdminResetModelForm(instance=row)
        return render(request, 'admin_change.html', {'form': form, 'title': '重置密码'})
    form = AdminResetModelForm(data=request.POST, instance=row)
    if form.is_valid():
        form.save()
        return redirect('/admin/list/')
    return render(request, 'admin_change.html', {'form': form, 'title': '重置密码'})


@permission_required('admin_delete')
def admin_delete(request, aid):
    """删除管理员"""
    models.Admin.objects.filter(id=aid).delete()
    return redirect('/admin/list/')


# ============ 角色管理 ============
@permission_required('role_view')
def role_list(request):
    q = request.GET.get('q', '')
    queryset = models.Role.objects.all()
    if q:
        queryset = queryset.filter(name__contains=q)
    total_count = queryset.count()
    page = Pagination(request, total_count)
    queryset = queryset[page.start_index:page.end_index]
    return render(request, 'role_list.html',
                  {'queryset': queryset, 'q': q, 'page_html': page.html()})


@permission_required('role_add')
def role_add(request):
    if request.method == 'GET':
        form = RoleModelForm()
        return render(request, 'role_change.html', {'form': form, 'title': '新建角色'})
    form = RoleModelForm(data=request.POST)
    if form.is_valid():
        form.save()
        return redirect('/role/list/')
    return render(request, 'role_change.html', {'form': form, 'title': '新建角色'})


@permission_required('role_edit')
def role_edit(request, rid):
    row = models.Role.objects.filter(id=rid).first()
    if request.method == 'GET':
        form = RoleModelForm(instance=row)
        return render(request, 'role_change.html', {'form': form, 'title': '编辑角色'})
    form = RoleModelForm(data=request.POST, instance=row)
    if form.is_valid():
        form.save()
        return redirect('/role/list/')
    return render(request, 'role_change.html', {'form': form, 'title': '编辑角色'})


@permission_required('role_delete')
def role_delete(request, rid):
    models.Role.objects.filter(id=rid).delete()
    return redirect('/role/list/')


# ============ 权限管理 ============
@permission_required('perm_view')
def perm_list(request):
    q = request.GET.get('q', '')
    queryset = models.Permission.objects.all()
    if q:
        queryset = queryset.filter(name__contains=q)
    total_count = queryset.count()
    page = Pagination(request, total_count)
    queryset = queryset[page.start_index:page.end_index]
    return render(request, 'perm_list.html',
                  {'queryset': queryset, 'q': q, 'page_html': page.html()})


@permission_required('perm_add')
def perm_add(request):
    if request.method == 'GET':
        form = PermissionModelForm()
        return render(request, 'perm_change.html', {'form': form, 'title': '新建权限'})
    form = PermissionModelForm(data=request.POST)
    if form.is_valid():
        form.save()
        return redirect('/perm/list/')
    return render(request, 'perm_change.html', {'form': form, 'title': '新建权限'})


@permission_required('perm_edit')
def perm_edit(request, pid):
    row = models.Permission.objects.filter(id=pid).first()
    if request.method == 'GET':
        form = PermissionModelForm(instance=row)
        return render(request, 'perm_change.html', {'form': form, 'title': '编辑权限'})
    form = PermissionModelForm(data=request.POST, instance=row)
    if form.is_valid():
        form.save()
        return redirect('/perm/list/')
    return render(request, 'perm_change.html', {'form': form, 'title': '编辑权限'})


@permission_required('perm_delete')
def perm_delete(request, pid):
    models.Permission.objects.filter(id=pid).delete()
    return redirect('/perm/list/')


# ============ 管理员分配角色（用户-角色关联） ============
@permission_required('admin_role')
def admin_role(request, aid):
    row = models.Admin.objects.filter(id=aid).first()
    if request.method == 'GET':
        form = AdminRoleModelForm(instance=row)
        return render(request, 'admin_role.html', {'form': form, 'row': row})
    form = AdminRoleModelForm(data=request.POST, instance=row)
    if form.is_valid():
        form.save()
        return redirect('/admin/list/')
    return render(request, 'admin_role.html', {'form': form, 'row': row})


# ============ 考勤管理 ============
@permission_required('attend_view')
def attend_list(request):
    q = request.GET.get('q', '')
    queryset = models.Attendance.objects.all()
    if q:
        queryset = queryset.filter(user__name__contains=q)
    total_count = queryset.count()
    page = Pagination(request, total_count)
    queryset = queryset[page.start_index:page.end_index]
    return render(request, 'attend_list.html',
                  {'queryset': queryset, 'q': q, 'page_html': page.html()})


@permission_required('attend_add')
def attend_add(request):
    if request.method == 'GET':
        form = AttendanceModelForm()
        return render(request, 'attend_change.html', {'form': form, 'title': '考勤登记'})
    form = AttendanceModelForm(data=request.POST)
    if form.is_valid():
        obj = form.save(commit=False)
        obj.status = obj.calc_status()  # 按打卡时间自动判定
        obj.save()
        return redirect('/attend/list/')
    return render(request, 'attend_change.html', {'form': form, 'title': '考勤登记'})


@permission_required('attend_edit')
def attend_edit(request, aid):
    row = models.Attendance.objects.filter(id=aid).first()
    if request.method == 'GET':
        form = AttendanceModelForm(instance=row)
        return render(request, 'attend_change.html', {'form': form, 'title': '编辑考勤'})
    form = AttendanceModelForm(data=request.POST, instance=row)
    if form.is_valid():
        obj = form.save(commit=False)
        obj.status = obj.calc_status()
        obj.save()
        return redirect('/attend/list/')
    return render(request, 'attend_change.html', {'form': form, 'title': '编辑考勤'})


@permission_required('attend_delete')
def attend_delete(request, aid):
    models.Attendance.objects.filter(id=aid).delete()
    return redirect('/attend/list/')


# ============ 薪资管理 ============
@permission_required('salary_view')
def salary_list(request):
    month = request.GET.get('month', '')
    user_id = request.GET.get('user', '')
    queryset = models.Salary.objects.all()
    if month:
        queryset = queryset.filter(month=month)
    if user_id:
        queryset = queryset.filter(user_id=user_id)

    # 月度总额统计（筛选范围内实发合计）
    total_actual = queryset.aggregate(s=Sum('actual'))['s'] or 0
    total_count = queryset.count()
    page = Pagination(request, total_count)
    queryset = queryset[page.start_index:page.end_index]

    return render(request, 'salary_list.html', {
        'queryset': queryset,
        'month': month,
        'user_id': int(user_id) if user_id else 0,
        'user_list': models.UserInfo.objects.all(),
        'total_actual': total_actual,
        'page_html': page.html(),
    })


@permission_required('salary_add')
def salary_add(request):
    if request.method == 'GET':
        form = SalaryModelForm()
        return render(request, 'salary_change.html', {'form': form, 'title': '薪资录入'})
    form = SalaryModelForm(data=request.POST)
    if form.is_valid():
        obj = form.save(commit=False)
        obj.actual = obj.calc_actual()  # 自动计算实发
        obj.save()
        return redirect('/salary/list/')
    return render(request, 'salary_change.html', {'form': form, 'title': '薪资录入'})


@permission_required('salary_edit')
def salary_edit(request, sid):
    row = models.Salary.objects.filter(id=sid).first()
    if request.method == 'GET':
        form = SalaryModelForm(instance=row)
        return render(request, 'salary_change.html', {'form': form, 'title': '编辑薪资'})
    form = SalaryModelForm(data=request.POST, instance=row)
    if form.is_valid():
        obj = form.save(commit=False)
        obj.actual = obj.calc_actual()
        obj.save()
        return redirect('/salary/list/')
    return render(request, 'salary_change.html', {'form': form, 'title': '编辑薪资'})


@permission_required('salary_delete')
def salary_delete(request, sid):
    models.Salary.objects.filter(id=sid).delete()
    return redirect('/salary/list/')


# ============ 公告管理 ============
@permission_required('ann_view')
def ann_list(request):
    q = request.GET.get('q', '')
    queryset = models.Announcement.objects.all()
    if q:
        queryset = queryset.filter(title__contains=q)
    # 置顶优先，再按发布时间倒序
    queryset = queryset.order_by('-is_top', '-publish_time')
    total_count = queryset.count()
    page = Pagination(request, total_count)
    queryset = queryset[page.start_index:page.end_index]
    return render(request, 'ann_list.html',
                  {'queryset': queryset, 'q': q, 'page_html': page.html()})


@permission_required('ann_add')
def ann_add(request):
    if request.method == 'GET':
        form = AnnouncementModelForm()
        return render(request, 'ann_change.html', {'form': form, 'title': '发布公告'})
    form = AnnouncementModelForm(data=request.POST)
    if form.is_valid():
        obj = form.save(commit=False)
        # 发布人自动取当前登录管理员，无需手选
        obj.publisher_id = request.session.get('info', {}).get('id')
        obj.save()
        return redirect('/ann/list/')
    return render(request, 'ann_change.html', {'form': form, 'title': '发布公告'})


@permission_required('ann_edit')
def ann_edit(request, nid):
    row = models.Announcement.objects.filter(id=nid).first()
    if request.method == 'GET':
        form = AnnouncementModelForm(instance=row)
        return render(request, 'ann_change.html', {'form': form, 'title': '编辑公告'})
    form = AnnouncementModelForm(data=request.POST, instance=row)
    if form.is_valid():
        form.save()
        return redirect('/ann/list/')
    return render(request, 'ann_change.html', {'form': form, 'title': '编辑公告'})


@permission_required('ann_delete')
def ann_delete(request, nid):
    models.Announcement.objects.filter(id=nid).delete()
    return redirect('/ann/list/')


# ============ 任务管理（AJAX 异步提交） ============
@permission_required('task_view')
def task_list(request):
    q = request.GET.get('q', '')
    queryset = models.Task.objects.all()
    if q:
        queryset = queryset.filter(title__contains=q)
    total_count = queryset.count()
    page = Pagination(request, total_count)
    queryset = queryset[page.start_index:page.end_index]
    add_form = TaskModelForm()  # 供弹窗使用的空表单
    return render(request, 'task_list.html',
                  {'queryset': queryset, 'q': q, 'add_form': add_form,
                   'page_html': page.html()})


@permission_required('task_add')
def task_add(request):
    """AJAX 新建：成功返回 status=True；校验失败返回字段级错误，前端不刷新回显"""
    form = TaskModelForm(data=request.POST)
    if form.is_valid():
        form.save()
        return JsonResponse({'status': True})
    return JsonResponse({'status': False, 'errors': form.errors}, status=400)


@permission_required('task_edit')
def task_edit(request, tid):
    row = models.Task.objects.filter(id=tid).first()
    if request.method == 'GET':
        form = TaskModelForm(instance=row)
        return render(request, 'task_change.html',
                      {'form': form, 'title': '编辑任务', 'tid': tid})
    form = TaskModelForm(data=request.POST, instance=row)
    if form.is_valid():
        form.save()
        return JsonResponse({'status': True})
    return JsonResponse({'status': False, 'errors': form.errors}, status=400)


@permission_required('task_delete')
def task_delete(request, tid):
    models.Task.objects.filter(id=tid).delete()
    return redirect('/task/list/')
