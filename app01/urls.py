from django.urls import path
from django.views.generic import RedirectView
from app01 import views

urlpatterns = [
    # 根路径自动跳登录页
    path('', RedirectView.as_view(url='/login/')),

    # 登录 / 退出
    path('login/', views.login),
    path('logout/', views.logout),
    path('image/code/', views.image_code),

    # 部门管理
    path('depart/list/', views.depart_list),
    path('depart/add/', views.depart_add),
    path('depart/<int:aid>/delete/', views.depart_delete),
    path('depart/<int:aid>/edit/', views.depart_edit),

    # 用户管理
    path('user/list/', views.user_list),
    path('user/add/', views.user_add),
    path('user/model/form/add/', views.user_model_form_add),
    path('user/<int:uid>/edit/', views.user_edit),
    path('user/<int:uid>/delete/', views.user_delete),

    # 靓号管理
    path('pretty/list/', views.pretty_list),
    path('pretty/add/', views.pretty_add),
    path('pretty/<int:pid>/edit/', views.pretty_edit),
    path('pretty/<int:pid>/delete/', views.pretty_delete),

    # 管理员管理
    path('admin/list/', views.admin_list),
    path('admin/add/', views.admin_add),
    path('admin/<int:aid>/edit/', views.admin_edit),
    path('admin/<int:aid>/reset/', views.admin_reset),
    path('admin/<int:aid>/role/', views.admin_role),
    path('admin/<int:aid>/delete/', views.admin_delete),

    # 角色管理
    path('role/list/', views.role_list),
    path('role/add/', views.role_add),
    path('role/<int:rid>/edit/', views.role_edit),
    path('role/<int:rid>/delete/', views.role_delete),

    # 权限管理
    path('perm/list/', views.perm_list),
    path('perm/add/', views.perm_add),
    path('perm/<int:pid>/edit/', views.perm_edit),
    path('perm/<int:pid>/delete/', views.perm_delete),

    # 考勤管理
    path('attend/list/', views.attend_list),
    path('attend/add/', views.attend_add),
    path('attend/<int:aid>/edit/', views.attend_edit),
    path('attend/<int:aid>/delete/', views.attend_delete),

    # 薪资管理
    path('salary/list/', views.salary_list),
    path('salary/add/', views.salary_add),
    path('salary/<int:sid>/edit/', views.salary_edit),
    path('salary/<int:sid>/delete/', views.salary_delete),

    # 公告管理
    path('ann/list/', views.ann_list),
    path('ann/add/', views.ann_add),
    path('ann/<int:nid>/edit/', views.ann_edit),
    path('ann/<int:nid>/delete/', views.ann_delete),

    # 任务管理（AJAX）
    path('task/list/', views.task_list),
    path('task/add/', views.task_add),
    path('task/<int:tid>/edit/', views.task_edit),
    path('task/<int:tid>/delete/', views.task_delete),
]

# ============ AI 智能助手（新增模块，独立视图文件，不改动上方任何现有路由）============
from app01 import views_ai
urlpatterns += [
    path('ai/', views_ai.ai_workbench),                 # 工作台页面
    path('ai/jd/', views_ai.gen_jd),                    # T2 招聘 JD
    path('ai/knowledge/', views_ai.knowledge_qa),      # T3 知识库问答
    path('ai/comment/', views_ai.data_comment),        # T4 数据点评
]

# ============ 9.md 第17/18/19/20/21 章新增功能（独立视图文件，不改动上方路由） ============
from app01 import views_ext
urlpatterns += [
    path('depart/multi/', views_ext.depart_multi),      # 17 Excel 批量导入部门
    # 18 订单管理
    path('order/list/', views_ext.order_list),
    path('order/add/', views_ext.order_add),
    path('order/delete/', views_ext.order_delete),
    path('order/detail/', views_ext.order_detail),
    path('order/edit/', views_ext.order_edit),
    # 19 数据统计 ECharts
    path('chart/list/', views_ext.chart_list),
    path('chart/bar/', views_ext.chart_bar),
    path('chart/pie/', views_ext.chart_pie),
    path('chart/line/', views_ext.chart_line),
    # 20 文件上传
    path('upload/list/', views_ext.upload_list),
    path('upload/form/', views_ext.upload_form),
    path('upload/modal/form/', views_ext.upload_modal_form),
    path('tt/', views_ext.tt),
    # 21 城市列表
    path('city/list/', views_ext.city_list),
    path('city/add/', views_ext.city_add),
]
