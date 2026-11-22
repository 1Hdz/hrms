from functools import wraps
from django.shortcuts import redirect
from django.http import HttpResponseForbidden


def login_required(view_func):
    """登录验证装饰器：未登录自动跳转到登录页"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        info = request.session.get('info')
        if not info:
            return redirect('/login/')
        return view_func(request, *args, **kwargs)
    return wrapper


def permission_required(perm_code):
    """接口级权限校验装饰器：
    - 未登录跳登录页
    - 超级管理员直接放行
    - 普通用户需拥有 perm_code 权限，否则返回 403
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            info = request.session.get('info')
            if not info:
                return redirect('/login/')
            if 'super_admin' in info.get('role_codes', []):
                return view_func(request, *args, **kwargs)
            if perm_code in info.get('perm_codes', []):
                return view_func(request, *args, **kwargs)
            return HttpResponseForbidden('<h3 style="text-align:center;">403：无权限访问该资源</h3>')
        return wrapper
    return decorator
