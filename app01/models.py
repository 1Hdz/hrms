from django.db import models
from django.utils import timezone

from app01.utils.scope import get_scope


class DeptScopeManager(models.Manager):
    """数据范围 Manager：根据当前请求自动过滤，只放行本部门数据。

    dept_lookup 指向"部门"在 ORM 里的过滤路径：
    - 员工表直接用 'depart_id'
    - 考勤/薪资/任务通过员工关联，用 'user__depart_id'
    """

    def __init__(self, dept_lookup, **kwargs):
        self.dept_lookup = dept_lookup
        super().__init__(**kwargs)

    def get_queryset(self):
        qs = super().get_queryset()
        scope = get_scope()
        # 超管、未登录、命令行脚本（无范围）：不限制
        if not scope or scope.get('is_super'):
            return qs
        depart_id = scope.get('depart_id')
        # 部门管理员未分配部门：看不到任何数据
        if not depart_id:
            return qs.none()
        return qs.filter(**{self.dept_lookup: depart_id})


class Department(models.Model):
    """部门表"""
    title = models.CharField(verbose_name='部门名称', max_length=16)

    def __str__(self):
        return self.title


class UserInfo(models.Model):
    """员工表"""
    name = models.CharField(verbose_name='姓名', max_length=16)
    password = models.CharField(verbose_name='密码', max_length=128)
    age = models.IntegerField(verbose_name='年龄')
    account = models.DecimalField(verbose_name='账户余额', max_digits=10, decimal_places=2, default=0)
    create_time = models.DateTimeField(verbose_name='入职时间', default=timezone.now)
    depart = models.ForeignKey(verbose_name='部门', to='Department', on_delete=models.SET_NULL, null=True, blank=True)
    gender_choices = (
        (1, '男'),
        (2, '女'),
    )
    gender = models.SmallIntegerField(verbose_name='性别', choices=gender_choices, default=1)
    mobile = models.CharField(verbose_name='手机号', max_length=11, unique=True,
                              null=True, blank=True)
    avatar = models.ImageField(verbose_name='头像', upload_to='avatar/%Y%m/',
                               null=True, blank=True)

    # 数据范围：部门管理员查询时自动只返回本部门员工
    objects = DeptScopeManager('depart_id')

    def __str__(self):
        return self.name


class PrettyNum(models.Model):
    """靓号表"""
    mobile = models.CharField(verbose_name='手机号', max_length=11)
    price = models.IntegerField(verbose_name='价格', default=0)
    level_choices = (
        (1, '领导'),
        (2, '队长'),
        (3, '部长'),
    )
    level = models.SmallIntegerField(verbose_name='级别', choices=level_choices, default=1)
    status_choices = (
        (1, '已占用'),
        (2, '未使用'),
    )
    status = models.SmallIntegerField(verbose_name='状态', choices=status_choices, default=2)

    def __str__(self):
        return self.mobile


class Admin(models.Model):
    """管理员表"""
    username = models.CharField(verbose_name='用户名', max_length=32)
    password = models.CharField(verbose_name='密码', max_length=128)
    # 用户-角色：多对多
    roles = models.ManyToManyField(verbose_name='角色', to='Role', blank=True)
    # 部门管理员所属部门（超管可留空）
    depart = models.ForeignKey(verbose_name='所属部门', to='Department',
                               on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.username


class Permission(models.Model):
    """权限表：菜单/按钮/接口"""
    type_choices = (
        (1, '菜单'),
        (2, '按钮'),
        (3, '接口'),
    )
    name = models.CharField(verbose_name='权限名称', max_length=32)
    code = models.CharField(verbose_name='权限编码', max_length=64, unique=True)
    type = models.SmallIntegerField(verbose_name='权限类型', choices=type_choices, default=2)
    resource = models.CharField(verbose_name='资源路径', max_length=128, blank=True, null=True)

    def __str__(self):
        return self.name


class Role(models.Model):
    """角色表：超级管理员/部门管理员/普通员工"""
    name = models.CharField(verbose_name='角色名称', max_length=32, unique=True)
    code = models.CharField(verbose_name='角色编码', max_length=32, unique=True)
    description = models.CharField(verbose_name='描述', max_length=128, blank=True, null=True)
    # 角色-权限：多对多
    permissions = models.ManyToManyField(verbose_name='拥有权限', to='Permission', blank=True)

    def __str__(self):
        return self.name


class Attendance(models.Model):
    """考勤表"""
    status_choices = (
        (1, '正常'),
        (2, '迟到'),
        (3, '早退'),
        (4, '缺勤'),
        (5, '请假'),
    )
    user = models.ForeignKey(verbose_name='员工', to='UserInfo', on_delete=models.CASCADE)
    att_date = models.DateField(verbose_name='考勤日期')
    check_in = models.DateTimeField(verbose_name='上班打卡时间', null=True, blank=True)
    check_out = models.DateTimeField(verbose_name='下班打卡时间', null=True, blank=True)
    status = models.SmallIntegerField(verbose_name='考勤状态', choices=status_choices, default=1)
    note = models.CharField(verbose_name='备注', max_length=128, blank=True, null=True)

    # 数据范围：按员工所属部门过滤
    objects = DeptScopeManager('user__depart_id')

    def __str__(self):
        return f'{self.user.name}-{self.att_date}'

    def calc_status(self):
        """根据打卡时间自动判定状态（标准 09:00 上班、18:00 下班）。
        请假优先；无上班打卡为缺勤；晚于 9 点为迟到；早于 18 点下班为早退。
        """
        from datetime import time
        if self.status == 5:
            return 5
        if not self.check_in:
            return 4
        is_late = self.check_in.time() > time(9, 0)
        is_early = bool(self.check_out) and self.check_out.time() < time(18, 0)
        if is_late:
            return 2
        if is_early:
            return 3
        return 1


class Salary(models.Model):
    """薪资表"""
    user = models.ForeignKey(verbose_name='员工', to='UserInfo', on_delete=models.CASCADE)
    month = models.CharField(verbose_name='所属月份', max_length=7)  # 如 2026-11
    base = models.DecimalField(verbose_name='基本工资', max_digits=10, decimal_places=2, default=0)
    performance = models.DecimalField(verbose_name='绩效奖金', max_digits=10, decimal_places=2, default=0)
    allowance = models.DecimalField(verbose_name='补贴', max_digits=10, decimal_places=2, default=0)
    deduction = models.DecimalField(verbose_name='扣款', max_digits=10, decimal_places=2, default=0)
    actual = models.DecimalField(verbose_name='实发工资', max_digits=12, decimal_places=2, default=0)

    # 数据范围：按员工所属部门过滤
    objects = DeptScopeManager('user__depart_id')

    def __str__(self):
        return f'{self.user.name}-{self.month}'

    def calc_actual(self):
        """实发 = 基本 + 绩效 + 补贴 - 扣款"""
        return self.base + self.performance + self.allowance - self.deduction


class Announcement(models.Model):
    """公告表"""
    title = models.CharField(verbose_name='公告标题', max_length=128)
    content = models.TextField(verbose_name='公告内容')
    publisher = models.ForeignKey(verbose_name='发布人', to='Admin',
                                  on_delete=models.SET_NULL, null=True, blank=True)
    is_top = models.BooleanField(verbose_name='是否置顶', default=False)
    publish_time = models.DateTimeField(verbose_name='发布时间', auto_now_add=True)

    def __str__(self):
        return self.title


class Task(models.Model):
    """任务表"""
    level_choices = (
        (1, '高优先级'),
        (2, '中优先级'),
        (3, '低优先级'),
    )
    status_choices = (
        (1, '待处理'),
        (2, '进行中'),
        (3, '已完成'),
    )
    title = models.CharField(verbose_name='任务标题', max_length=128)
    level = models.SmallIntegerField(verbose_name='级别', choices=level_choices, default=2)
    content = models.TextField(verbose_name='任务内容', blank=True, null=True)
    user = models.ForeignKey(verbose_name='负责人', to='UserInfo', on_delete=models.CASCADE)
    deadline = models.DateTimeField(verbose_name='截止时间', blank=True, null=True)
    status = models.SmallIntegerField(verbose_name='任务状态', choices=status_choices, default=1)
    create_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)

    # 数据范围：按负责人所属部门过滤
    objects = DeptScopeManager('user__depart_id')

    def __str__(self):
        return self.title


class Knowledge(models.Model):
    """T3：制度知识库（考勤、报销、请假等制度条目），全公司通用，不做部门隔离"""
    title = models.CharField(verbose_name='标题', max_length=128)
    content = models.TextField(verbose_name='内容')
    create_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)

    class Meta:
        verbose_name = '制度知识'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.title


# ============ 以下为 9.md 第18/20/21 章新增模型（独立功能，不做部门隔离，沿用默认 Manager） ============
class Order(models.Model):
    """订单（第18章）"""
    oid = models.CharField(verbose_name='订单号', max_length=64)
    title = models.CharField(verbose_name='名称', max_length=32)
    price = models.IntegerField(verbose_name='价格')
    status_choices = (
        (1, '待支付'),
        (2, '已支付'),
    )
    status = models.SmallIntegerField(verbose_name='状态',
                                     choices=status_choices, default=1)
    admin = models.ForeignKey(verbose_name='管理员', to='Admin',
                              on_delete=models.CASCADE)

    def __str__(self):
        return self.oid


class Boss(models.Model):
    """老板（第20章 Form 上传，头像用 CharField 存相对路径）"""
    name = models.CharField(verbose_name='姓名', max_length=32)
    age = models.IntegerField(verbose_name='年龄')
    img = models.CharField(verbose_name='头像', max_length=128)

    def __str__(self):
        return self.name


class City(models.Model):
    """城市（第21章，FileField 自动存文件，数据库存相对路径）"""
    name = models.CharField(verbose_name='名称', max_length=32)
    count = models.IntegerField(verbose_name='人口')
    img = models.FileField(verbose_name='Logo', max_length=128, upload_to='city/')

    def __str__(self):
        return self.name


class XX(models.Model):
    """头像预览示例（第20章，FileField + 前端预览）"""
    title = models.CharField(verbose_name='名称', max_length=32)
    image = models.FileField(verbose_name='头像', upload_to='avatar/')

    def __str__(self):
        return self.title
