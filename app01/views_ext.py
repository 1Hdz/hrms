"""9.md 第17/18/19/20/21 章新增功能视图（独立文件，不改动 views.py）。

所有新功能集中在此：
- 第17章：Excel 批量导入部门
- 第18章：订单管理（AJAX + JSON）
- 第19章：ECharts 数据统计（后端出 JSON）
- 第20/21章：文件上传、城市列表
"""
import os
import random
from datetime import datetime

from django import forms
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.conf import settings

from app01 import models
from app01.forms import BootStrapModelForm
from app01.utils.auth import login_required


# ==================== 第17章：Excel 批量导入部门 ====================
@login_required
def depart_multi(request):
    """读取上传的 Excel，第一列从第 2 行起为部门名，重复名称不插入。"""
    from openpyxl import load_workbook
    file_object = request.FILES.get('exc')
    if not file_object:  # 未选文件直接提交：回到列表，不报错
        return redirect('/depart/list/')
    wb = load_workbook(file_object)
    sheet = wb.worksheets[0]
    for row in sheet.iter_rows(min_row=2):
        text = row[0].value
        if text is None:
            continue
        text = str(text).strip()
        if text and not models.Department.objects.filter(title=text).exists():
            models.Department.objects.create(title=text)
    return redirect('/depart/list/')


# ==================== 第18章：订单管理（AJAX + JSON，正常 CSRF 校验） ====================
from app01.utils.pagination import Pagination


class OrderModelForm(BootStrapModelForm):
    class Meta:
        model = models.Order
        exclude = ['oid', 'admin']  # 订单号、管理员由后端生成，不让用户填


@login_required
def order_list(request):
    """订单列表：分页 + 空表单（弹窗用）"""
    queryset = models.Order.objects.all().order_by('-id')
    total_count = queryset.count()
    page = Pagination(request, total_count)
    context = {
        'form': OrderModelForm(),
        'queryset': queryset[page.start_index:page.end_index],
        'page_html': page.html(),
    }
    return render(request, 'order_list.html', context)


@login_required
def order_add(request):
    """新建订单：订单号自动生成，管理员取当前登录人。"""
    form = OrderModelForm(data=request.POST)
    if form.is_valid():
        form.instance.oid = datetime.now().strftime('%Y%m%d%H%M%S') + str(random.randint(1000, 9999))
        form.instance.admin_id = request.session['info']['id']
        form.save()
        return JsonResponse({'status': True})
    return JsonResponse({'status': False, 'error': form.errors})


@login_required
def order_delete(request):
    """删除订单。"""
    uid = request.GET.get('uid')
    if not models.Order.objects.filter(id=uid).exists():
        return JsonResponse({'status': False, 'error': '删除失败，数据不存在。'})
    models.Order.objects.filter(id=uid).delete()
    return JsonResponse({'status': True})


@login_required
def order_detail(request):
    """根据 ID 获取订单详情，供弹窗回填。"""
    uid = request.GET.get('uid')
    row_dict = models.Order.objects.filter(id=uid).values('title', 'price', 'status').first()
    if not row_dict:
        return JsonResponse({'status': False, 'error': '数据不存在。'})
    return JsonResponse({'status': True, 'data': row_dict})


@login_required
def order_edit(request):
    """编辑订单。"""
    uid = request.GET.get('uid')
    row_object = models.Order.objects.filter(id=uid).first()
    if not row_object:
        return JsonResponse({'status': False, 'tips': '数据不存在，请刷新重试。'})
    form = OrderModelForm(data=request.POST, instance=row_object)
    if form.is_valid():
        form.save()
        return JsonResponse({'status': True})
    return JsonResponse({'status': False, 'error': form.errors})


# ==================== 第19章：数据统计 ECharts（后端出数据，前端出图） ====================
@login_required
def chart_list(request):
    """数据统计页面。"""
    return render(request, 'chart_list.html')


@login_required
def chart_bar(request):
    """柱状图数据。"""
    result = {
        'status': True,
        'data': {
            'legend': ['梁吉宁', '武沛齐'],
            'series_list': [
                {'name': '梁吉宁', 'type': 'bar', 'data': [15, 20, 36, 10, 10, 10]},
                {'name': '武沛齐', 'type': 'bar', 'data': [45, 10, 66, 40, 20, 50]},
            ],
            'x_axis': ['1月', '2月', '4月', '5月', '6月', '7月'],
        },
    }
    return JsonResponse(result)


@login_required
def chart_pie(request):
    """饼图数据。"""
    data = [
        {'value': 2048, 'name': 'IT部门'},
        {'value': 1735, 'name': '运营'},
        {'value': 580, 'name': '新媒体'},
    ]
    return JsonResponse({'status': True, 'data': data})


@login_required
def chart_line(request):
    """折线图数据。"""
    result = {
        'status': True,
        'data': {
            'legend': ['上海', '广西'],
            'series_list': [
                {'name': '上海', 'type': 'line', 'data': [15, 20, 36, 10, 10, 10]},
                {'name': '广西', 'type': 'line', 'data': [45, 10, 66, 40, 20, 50]},
            ],
            'x_axis': ['1月', '2月', '4月', '5月', '6月', '7月'],
        },
    }
    return JsonResponse(result)


# ==================== 第20/21章：文件上传 + 城市 ====================
from django.http import HttpResponse


class _BootStrapControl:
    """混入：统一加 form-control；bootstrap_exclude_fields 里的字段（文件框）不套样式。"""
    bootstrap_exclude_fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name in self.bootstrap_exclude_fields:
                continue
            if field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'
                field.widget.attrs['placeholder'] = field.label
            else:
                field.widget.attrs = {'class': 'form-control', 'placeholder': field.label}


class BootStrapForm(_BootStrapControl, forms.Form):
    """普通 Form 版（第20章手动上传用）。"""
    pass


class FileModelForm(_BootStrapControl, forms.ModelForm):
    """ModelForm 版，支持文件字段排除。"""
    pass


# ---------- 20.1 原始方式：chunks 分块写盘 ----------
@login_required
def upload_list(request):
    if request.method == 'GET':
        return render(request, 'upload_list.html')
    file_object = request.FILES.get('avatar')
    if not file_object:
        return render(request, 'upload_list.html')
    target = os.path.join(settings.BASE_DIR, file_object.name)
    with open(target, 'wb') as f:
        for chunk in file_object.chunks():
            f.write(chunk)
    return HttpResponse('上传成功：' + file_object.name)


# ---------- 20.2 普通 Form 上传（Boss 表，手动写文件） ----------
class UpForm(BootStrapForm):
    bootstrap_exclude_fields = ['img']
    name = forms.CharField(label='姓名')
    age = forms.IntegerField(label='年龄')
    img = forms.FileField(label='头像')


@login_required
def upload_form(request):
    title = 'Form 上传（Boss 表，手动写文件）'
    if request.method == 'GET':
        return render(request, 'upload_form.html', {'form': UpForm(), 'title': title})
    form = UpForm(request.POST, request.FILES)
    if form.is_valid():
        image_object = form.cleaned_data['img']
        boss_dir = os.path.join(settings.MEDIA_ROOT, 'boss')
        os.makedirs(boss_dir, exist_ok=True)
        with open(os.path.join(boss_dir, image_object.name), 'wb') as f:
            for chunk in image_object.chunks():
                f.write(chunk)
        models.Boss.objects.create(
            name=form.cleaned_data['name'],
            age=form.cleaned_data['age'],
            img='boss/' + image_object.name)
        return HttpResponse('上传成功')
    return render(request, 'upload_form.html', {'form': form, 'title': title})


# ---------- 20.3 / 21  ModelForm 上传（City 表，文件自动保存） ----------
class CityModelForm(FileModelForm):
    bootstrap_exclude_fields = ['img']

    class Meta:
        model = models.City
        fields = '__all__'


@login_required
def upload_modal_form(request):
    title = 'ModelForm 上传（City 表，文件自动保存）'
    if request.method == 'GET':
        return render(request, 'upload_form.html', {'form': CityModelForm(), 'title': title})
    form = CityModelForm(request.POST, request.FILES)
    if form.is_valid():
        form.save()
        return HttpResponse('上传成功')
    return render(request, 'upload_form.html', {'form': form, 'title': title})


# ---------- 20.4 头像预览（XX 表） ----------
class XXModelForm(FileModelForm):
    bootstrap_exclude_fields = ['image']

    class Meta:
        model = models.XX
        fields = '__all__'


@login_required
def tt(request):
    if request.method == 'GET':
        return render(request, 'tt.html', {'form': XXModelForm()})
    form = XXModelForm(request.POST, request.FILES)
    if form.is_valid():
        form.save()
    return render(request, 'tt.html', {'form': form})


# ---------- 21 城市列表 / 新建 ----------
@login_required
def city_list(request):
    return render(request, 'city_list.html',
                  {'queryset': models.City.objects.all()})


@login_required
def city_add(request):
    title = '新建城市'
    if request.method == 'GET':
        return render(request, 'upload_form.html', {'form': CityModelForm(), 'title': title})
    form = CityModelForm(request.POST, request.FILES)
    if form.is_valid():
        form.save()
        return redirect('/city/list/')
    return render(request, 'upload_form.html', {'form': form, 'title': title})
