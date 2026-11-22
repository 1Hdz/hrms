# -*- coding: utf-8 -*-
"""数据范围（数据级权限）工具

用 thread-local 记录"当前这一次请求"的数据范围，自定义 Manager 据此自动过滤，
于是视图里原有的 .objects.all() 一行都不用改，就能让部门管理员只看到本部门数据。

- 超级管理员 / 未登录 / 命令行脚本：不限制，返回全部
- 部门管理员：只返回其所属部门相关的数据
"""
import re
import threading

from django.http import HttpResponseForbidden

_local = threading.local()


def set_scope(is_super=False, depart_id=None):
    """记录当前请求的数据范围"""
    _local.scope = {'is_super': is_super, 'depart_id': depart_id}


def get_scope():
    """读取当前数据范围；非请求环境（命令行等）返回 None"""
    return getattr(_local, 'scope', None)


def clear_scope():
    """请求结束后清理，避免线程复用时串数据"""
    if hasattr(_local, 'scope'):
        del _local.scope


# 受保护的"单条对象"路由：(路径正则, 对应模型名)
_PROTECT_RULES = (
    (re.compile(r'^/user/(\d+)/(edit|delete)/'), 'UserInfo'),
    (re.compile(r'^/attend/(\d+)/(edit|delete)/'), 'Attendance'),
    (re.compile(r'^/salary/(\d+)/(edit|delete)/'), 'Salary'),
    (re.compile(r'^/task/(\d+)/(edit|delete)/'), 'Task'),
)


def object_allowed(request):
    """部门管理员直接访问某条对象时，校验它是否属于本部门。
    超管不拦；匹配不到规则的普通页面不拦。
    """
    info = request.session.get('info')
    if not info or 'super_admin' in info.get('role_codes', []):
        return True
    for pattern, model_name in _PROTECT_RULES:
        match = pattern.match(request.path)
        if match:
            from app01 import models
            model = getattr(models, model_name)
            # objects 已带部门过滤，跨部门 id 查不到
            return model.objects.filter(id=match.group(1)).exists()
    return True


class ScopeMiddleware:
    """识别当前登录管理员的角色与所属部门，写入 thread-local"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        info = request.session.get('info')
        if info:
            role_codes = info.get('role_codes', [])
            is_super = 'super_admin' in role_codes
            depart_id = None
            if not is_super:
                # 延迟导入避免循环依赖；Admin 表本身不做部门过滤
                from app01.models import Admin
                admin = Admin.objects.filter(id=info.get('id')).first()
                if admin:
                    depart_id = admin.depart_id
            set_scope(is_super=is_super, depart_id=depart_id)
            # 对象级越权拦截：直接改 URL 操作别部门数据 → 403
            if not object_allowed(request):
                clear_scope()
                return HttpResponseForbidden(
                    '<h3 style="text-align:center;">403：无权操作其他部门数据</h3>')
        try:
            response = self.get_response(request)
        finally:
            clear_scope()
        return response

