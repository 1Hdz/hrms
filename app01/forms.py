
from django import forms
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import make_password, check_password
from app01 import models


class BootStrapModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'
                field.widget.attrs['placeholder'] = field.label
            else:
                field.widget.attrs = {
                    'class': 'form-control',
                    'placeholder': field.label,
                }


class UserModelForm(BootStrapModelForm):
    # 手机号：覆盖默认字段，加正则校验
    mobile = forms.CharField(
        label="手机号",
        validators=[RegexValidator(r'^1[3-9]\d{9}$', '手机号格式错误')],
    )

    class Meta:
        model = models.UserInfo
        fields = ['name', 'password', 'age', 'account', 'create_time',
                  'gender', 'depart', 'mobile', 'avatar']

    def clean_name(self):
        """姓名长度校验"""
        name = self.cleaned_data['name']
        if not 2 <= len(name) <= 16:
            raise ValidationError('姓名长度需在 2~16 个字符之间')
        return name

    def clean_age(self):
        """年龄范围校验"""
        age = self.cleaned_data['age']
        if not 18 <= age <= 65:
            raise ValidationError('年龄需在 18~65 岁之间')
        return age

    def clean_password(self):
        """密码使用 Django 安全哈希存储"""
        return make_password(self.cleaned_data['password'])

    def clean_mobile(self):
        """手机号唯一校验：编辑时排除自身"""
        mobile = self.cleaned_data['mobile']
        qs = models.UserInfo.objects.filter(mobile=mobile)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError('手机号已存在')
        return mobile


class PrettyModelForm(BootStrapModelForm):
    # 手机号格式校验：1开头，第二位3-9，共11位
    mobile = forms.CharField(
        label="手机号",
        validators=[RegexValidator(r'^1[3-9]\d{9}$', '手机号格式错误')],
    )

    class Meta:
        model = models.PrettyNum
        fields = ['mobile', 'price', 'level', 'status']

    def clean_mobile(self):
        """新增时校验手机号是否已存在"""
        txt_mobile = self.cleaned_data['mobile']
        exists = models.PrettyNum.objects.filter(mobile=txt_mobile).exists()
        if exists:
            raise ValidationError("手机号已存在")
        return txt_mobile


class PrettyEditModelForm(BootStrapModelForm):
    mobile = forms.CharField(
        label="手机号",
        validators=[RegexValidator(r'^1[3-9]\d{9}$', '手机号格式错误')],
    )

    class Meta:
        model = models.PrettyNum
        fields = ['mobile', 'price', 'level', 'status']

    def clean_mobile(self):
        """编辑时校验手机号重复（排除自己）"""
        txt_mobile = self.cleaned_data['mobile']
        exists = (models.PrettyNum.objects.exclude(id=self.instance.pk)
                  .filter(mobile=txt_mobile).exists())
        if exists:
            raise ValidationError("手机号已存在")
        return txt_mobile


# ============ 登录（带图片验证码） ============
class LoginForm(forms.Form):
    """登录表单：用户名 + 密码 + 图片验证码"""
    username = forms.CharField(
        label="用户名",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '用户名'}),
        required=True,
    )
    password = forms.CharField(
        label="密码",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '密码'}),
        required=True,
    )
    code = forms.CharField(
        label="图片验证码",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '不区分大小写'}),
        required=True,
    )


# ============ 管理员 ============
class AdminModelForm(BootStrapModelForm):
    """新增管理员：用户名 + 密码 + 确认密码"""
    confirm_password = forms.CharField(
        label="确认密码",
        widget=forms.PasswordInput,
    )

    class Meta:
        model = models.Admin
        fields = ['username', 'password', 'confirm_password']
        widgets = {
            'password': forms.PasswordInput,
        }

    def clean(self):
        """校验两次密码一致，再对密码做安全哈希"""
        cleaned = super().clean()
        pwd = cleaned.get('password')
        confirm = cleaned.get('confirm_password')
        if pwd and confirm and pwd != confirm:
            self.add_error('confirm_password', '两次密码不一致')
        if pwd:
            cleaned['password'] = make_password(pwd)
        return cleaned


class AdminEditModelForm(BootStrapModelForm):
    """编辑管理员：可改用户名；部门管理员可分配所属部门"""
    class Meta:
        model = models.Admin
        fields = ['username', 'depart']


class AdminResetModelForm(BootStrapModelForm):
    """重置密码：新密码 + 确认密码"""
    confirm_password = forms.CharField(
        label="确认密码",
        widget=forms.PasswordInput,
    )

    class Meta:
        model = models.Admin
        fields = ['password', 'confirm_password']
        widgets = {
            'password': forms.PasswordInput,
        }

    def clean(self):
        """校验两次一致、新密码不能与旧密码相同，再做安全哈希"""
        cleaned = super().clean()
        pwd = cleaned.get('password')
        confirm = cleaned.get('confirm_password')
        if pwd and confirm and pwd != confirm:
            self.add_error('confirm_password', '两次密码不一致')
        if pwd:
            if check_password(pwd, self.instance.password):
                self.add_error('password', '新密码不能与旧密码相同')
            cleaned['password'] = make_password(pwd)
        return cleaned


# ============ 角色 / 权限 ============
class RoleModelForm(BootStrapModelForm):
    """角色表单：含角色-权限多选关联"""
    class Meta:
        model = models.Role
        fields = ['name', 'code', 'description', 'permissions']


class PermissionModelForm(BootStrapModelForm):
    """权限表单"""
    class Meta:
        model = models.Permission
        fields = ['name', 'code', 'type', 'resource']


class AdminRoleModelForm(BootStrapModelForm):
    """给管理员分配角色（用户-角色关联）"""
    class Meta:
        model = models.Admin
        fields = ['roles']


# ============ 考勤 ============
class AttendanceModelForm(BootStrapModelForm):
    class Meta:
        model = models.Attendance
        fields = ['user', 'att_date', 'check_in', 'check_out', 'status', 'note']


# ============ 薪资 ============
class SalaryModelForm(BootStrapModelForm):
    class Meta:
        model = models.Salary
        fields = ['user', 'month', 'base', 'performance', 'allowance', 'deduction']


# ============ 公告 ============
class AnnouncementModelForm(BootStrapModelForm):
    class Meta:
        model = models.Announcement
        fields = ['title', 'content', 'is_top']


# ============ 任务 ============
class TaskModelForm(BootStrapModelForm):
    class Meta:
        model = models.Task
        fields = ['title', 'level', 'content', 'user', 'deadline', 'status']

