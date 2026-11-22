# -*- coding: utf-8 -*-
from django import template

from app01.utils.scope import get_scope

register = template.Library()


@register.simple_tag
def has_perm(request, code):
    """按钮级权限：判断当前登录用户是否拥有某权限码。
    超级管理员直接放行，其余按 session 中的权限码判断。
    """
    info = request.session.get('info', {})
    if 'super_admin' in info.get('role_codes', []):
        return True
    return code in info.get('perm_codes', [])


@register.filter
def mask_money(value):
    """金额脱敏：部门管理员看到掩码，超级管理员看真实数字"""
    scope = get_scope()
    if scope and not scope.get('is_super'):
        return '****'
    return value

