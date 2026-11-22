# 企业员工管理系统 HRMS

基于 **Django 5.2 + MySQL** 从零搭建的企业级员工管理系统，覆盖组织人事、考勤薪资、公告任务等完整业务流程，并通过调用**现成的大模型 API** 实现了一个可演示、可答辩的 AI 智能助手模块。项目采用 MTV 架构，前端静态资源全部本地化，无需联网即可运行。

- 后端：Django 5.2.17、Django ORM、Session 认证
- 数据库：MySQL 8.0（PyMySQL 驱动）
- 前端：Bootstrap 3.4、jQuery、ECharts 5.5（均为本地静态资源）
- 智能能力：OpenAI 兼容大模型接口（默认接入硅基流动 Qwen3-VL）

---

## 一、功能特性

### 基础业务模块
- **登录认证**：用户名 + 密码 + 图片验证码，密码使用 Django 哈希加密存储，Session 维持登录态
- **RBAC 权限**：管理员 — 角色 — 权限三层模型，多对多授权，支持菜单 / 按钮 / 接口三类权限，接口级装饰器 + 模板标签双重校验
- **部门管理**：完整 CRUD，支持 **Excel 批量导入**（openpyxl，自动跳过空行与重复名称）
- **员工管理**：完整 CRUD，原生表单与 ModelForm 两种新增方式，头像上传、手机号校验、分页
- **靓号管理**：号码搜索、级别分类、分页、手机号正则与重复校验
- **考勤管理**：上 / 下班打卡，根据打卡时间**自动判定**正常 / 迟到 / 早退 / 缺勤 / 请假
- **薪资管理**：基本 + 绩效 + 补贴 − 扣款，**自动核算实发工资**，非超管查看时金额脱敏
- **公告管理**：发布、置顶、编辑、删除
- **任务管理**：AJAX 无刷新操作，优先级与状态流转
- **订单管理**：AJAX 弹窗增删改查，订单号自动生成、管理员自动关联
- **数据统计**：ECharts 折线图、柱状图、饼图，后端出 JSON、前端渲染
- **文件上传**：原始 chunks 写盘、Form 手动写、ModelForm 自动存、FileReader 本地预览四种方式
- **城市管理**：城市列表 + Logo 上传

### 核心亮点
1. **数据范围控制**：部门管理员登录后只能看到**本部门**员工及其考勤、薪资、任务，超管不限制（见下文）。
2. **AI 智能助手**：调用大模型 API 实现招聘 JD 生成、制度知识库问答（RAG 雏形）、数据智能点评。
3. **密钥零泄露**：API Key 只放在项目根 `.env`，`.env` 已被 `.gitignore` 忽略，代码中不写死任何密钥。

---

## 二、数据权限设计（部门数据隔离）

系统通过自定义 Manager 实现**透明的行级数据过滤**，业务视图无需手写过滤条件。

- `app01/utils/scope.py`：基于 thread-local 保存当前登录人的范围信息（是否超管、所属部门 ID）。
- `app01/models.py` 中的 `DeptScopeManager`：重写 `get_queryset()`，按当前请求自动过滤
  - 超管 / 未登录 / 命令行脚本：不限制
  - 部门管理员：只返回本部门数据；未分配部门时返回空集
  - 过滤路径可配置：员工表用 `depart_id`，考勤 / 薪资 / 任务通过员工关联用 `user__depart_id`
- 挂接该 Manager 的模型：`UserInfo`、`Attendance`、`Salary`、`Task`。

> 效果：部门管理员无法跨部门管理员工，也无法看到其他部门的薪资明细。

---

## 三、AI 智能助手

统一封装在 `app01/utils/ai.py` 的 `LLMClient`，把大模型抽象成「给文字、返回文字」的接口，底层调用 OpenAI 兼容的 `/chat/completions`，任何网络 / 认证异常都会转成友好提示，不会让页面崩溃。

| 编号 | 功能 | 视图 | 实现要点 |
| --- | --- | --- | --- |
| T1 | 统一调用客户端 | `utils/ai.py` | 从环境变量读取 Key / Base URL / Model，模块级单例复用 |
| T2 | 智能生成招聘 JD | `views_ai.gen_jd` | 三段式提示词（角色 + 要求 + 输出格式），输出职责 / 任职要求 / 薪资范围 |
| T3 | 制度知识库问答 | `views_ai.knowledge_qa` | **RAG 雏形**：先按关键词检索 `Knowledge` 表，把命中制度拼进提示词，限定只能依据资料回答，无资料直接回答「不知道」 |
| T4 | 数据智能点评 | `views_ai.data_comment` | 读取员工真实考勤 / 薪资，薪资按角色脱敏，输出点评与改进建议 |

T3 检索流程：从问题中提取「考勤 / 请假 / 报销 / 加班 / 转正」等领域关键词 → 在知识库标题与内容中匹配 → 命中条目作为上下文（context）交给大模型 → 模型仅基于该上下文作答，避免凭空编造。

---

## 四、数据模型

模型定义于 `app01/models.py`，共 14 张业务表：

| 模型 | 说明 | 关键字段 |
| --- | --- | --- |
| Department | 部门 | title |
| UserInfo | 员工 | name、age、gender、mobile、avatar、depart(FK) |
| PrettyNum | 靓号 | mobile、price、level、status |
| Admin | 管理员 | username、password、roles(M2M)、depart(FK) |
| Role | 角色 | name、code、permissions(M2M) |
| Permission | 权限 | name、code、type、resource |
| Attendance | 考勤 | user(FK)、att_date、check_in/out、status |
| Salary | 薪资 | user(FK)、month、base、performance、allowance、deduction、actual |
| Announcement | 公告 | title、content、publisher(FK)、is_top |
| Task | 任务 | title、level、status、user(FK)、deadline |
| Knowledge | 制度知识库 | title、content |
| Order | 订单 | oid、title、price、status、admin(FK) |
| Boss | 上传示例（Form） | name、age、img(相对路径) |
| City | 城市 | name、count、img(FileField) |
| XX | 头像预览示例 | title、image(FileField) |

---

## 五、项目结构

```
ems/
├── manage.py                     # Django 管理入口
├── requirements.txt              # 依赖清单
├── .env                          # 环境变量（含 API Key，不入库）
├── _seed_data.py                 # 演示数据填充脚本（幂等，可重复运行）
├── init_knowledge.py             # 初始化制度知识库
├── ems/                          # 项目配置
│   ├── settings.py               # 全局配置（MySQL、静态/媒体文件、中文时区）
│   ├── urls.py                   # 全局路由（含 media 访问）
│   └── __init__.py               # 安装 PyMySQL 为 MySQLdb
├── media/                        # 用户上传与演示图片
│   ├── city/  boss/  avatar/
└── app01/                        # 业务应用
    ├── models.py                 # 数据模型 + DeptScopeManager
    ├── views.py                  # 基础业务视图
    ├── views_ai.py               # AI 助手视图（T2/T3/T4）
    ├── views_ext.py              # 订单/图表/上传/城市等扩展视图
    ├── forms.py                  # ModelForm 与登录表单
    ├── urls.py                   # 子路由（分模块追加）
    ├── utils/
    │   ├── ai.py                 # 大模型客户端 LLMClient
    │   ├── auth.py               # login_required / permission_required
    │   ├── scope.py              # 数据范围（thread-local）
    │   ├── code.py               # 图片验证码
    │   └── pagination.py         # 通用分页组件
    ├── templatetags/rbac.py      # 权限模板标签
    ├── migrations/               # 数据库迁移（0001–0014）
    ├── templates/                # 全部 HTML 模板
    └── static/                   # 本地静态资源
        ├── js/  (jquery、echarts)
        ├── css/ (theme)
        └── plugins/ (bootstrap、datepicker)
```

---

## 六、快速开始

### 1. 环境要求
- Python 3.10+
- MySQL 8.0（服务已启动）

### 2. 获取代码并安装依赖
```bash
git clone https://github.com/1Hdz/hrms.git
cd hrms
python -m pip install -r requirements.txt
```

### 3. 创建数据库
登录 MySQL 后执行：
```sql
CREATE DATABASE ems DEFAULT CHARACTER SET utf8mb4;
```
数据库连接配置位于 `ems/settings.py`，默认 `root / 123456 / 127.0.0.1:3306`，请按本地环境修改。

### 4. 配置环境变量（AI 功能需要）
在项目根目录新建 `.env`（可参考 `.env.example`）：
```ini
LLM_API_KEY=你的大模型API密钥
LLM_BASE_URL=https://api.siliconflow.cn/v1
LLM_MODEL=Qwen/Qwen3-VL-8B-Instruct
```
> 不配置 `.env` 不影响基础业务，仅 AI 功能会返回「服务不可用」提示。

### 5. 执行迁移
```bash
python manage.py migrate
```

### 6. 创建超级管理员（首次）
```bash
python manage.py shell
```
```python
from app01.models import Admin, Role
from django.contrib.auth.hashers import make_password
obj = Admin.objects.create(username="admin", password=make_password("admin123"))
obj.roles.add(Role.objects.get(code="super_admin"))   # 关联超级管理员角色
```
也可在登录后通过「管理员管理」页面创建账号并分配角色。

### 7.（可选）初始化演示数据
```bash
python init_knowledge.py     # 6 条制度知识
python _seed_data.py         # 城市 / Boss / 头像 / 订单演示数据（幂等）
```

### 8. 启动服务
```bash
python manage.py runserver
```
浏览器访问 <http://127.0.0.1:8000/>，自动跳转登录页。

---

## 七、常见问题

| 现象 | 原因与解决 |
| --- | --- |
| `No module named 'pymysql'` | 依赖未安装，执行 `pip install -r requirements.txt` |
| `(1045) Access denied` | MySQL 账号密码错误，核对 `settings.py` 中连接配置 |
| `(2003) Can't connect` | MySQL 服务未启动，先启动 MySQL |
| `(1049) Unknown database 'ems'` | 数据库未创建，先执行建库语句 |
| 验证码一直错误 | 验证码区分大小写，按图片输入对应字符 |
| AI 回答「服务不可用」 | 检查 `.env` 中 Key / Base URL / Model 是否正确、网络是否可达、账户是否有额度 |
| 页面样式丢失 | 确认 `app01/static/` 结构完整、`STATICFILES_DIRS` 配置正确 |
| 8000 端口被占用 | 换端口：`python manage.py runserver 8001` |

---

## 八、备注

- 本项目为课程设计 / 学习项目，所有静态资源已本地化，离线可用。
- `SECRET_KEY` 与 `DEBUG=True` 均为开发环境配置，**生产部署前必须更换密钥并关闭 DEBUG**。
- 数据库密码、API 密钥等敏感信息请勿提交到公开仓库。
