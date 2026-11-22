"""为新板块填充演示数据（可重复运行，已存在的名称不会重复插入）。"""
import os
import sys
from datetime import datetime

sys.path.insert(0, r"E:\DjangoProject\ems")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ems.settings")
import django
django.setup()

from PIL import Image, ImageDraw, ImageFont
from django.conf import settings
from app01 import models

FONT_PATH = r"C:\Windows\Fonts\msyh.ttc"


def make_image(path, text, bg, size=200, fg=(255, 255, 255), font_size=80):
    """生成一张纯色背景 + 居中文字的 PNG。"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img = Image.new("RGB", (size, size), bg)
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype(FONT_PATH, font_size)
    except Exception:
        font = ImageFont.load_default()
    bbox = d.textbbox((0, 0), text, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    d.text(((size - w) / 2 - bbox[0], (size - h) / 2 - bbox[1]),
           text, fill=fg, font=font)
    img.save(path)


# ---------------- 城市（City，含 Logo） ----------------
CITIES = [
    ("北京", 2189, (192, 57, 43)),
    ("上海", 2487, (41, 128, 185)),
    ("广州", 1881, (39, 174, 96)),
    ("深圳", 1768, (142, 68, 173)),
    ("成都", 2126, (211, 84, 0)),
    ("杭州", 1237, (22, 160, 133)),
]
for name, count, color in CITIES:
    rel = "city/%s.png" % name
    if not models.City.objects.filter(name=name).exists():
        make_image(os.path.join(settings.MEDIA_ROOT, rel), name, color, font_size=64)
        models.City.objects.create(name=name, count=count, img=rel)

# ---------------- 部门主管（Boss，含头像） ----------------
BOSSES = [
    ("张伟", 42, (52, 73, 94)),
    ("李娜", 38, (155, 89, 182)),
    ("王强", 45, (39, 174, 96)),
    ("赵敏", 35, (230, 126, 34)),
    ("陈杰", 50, (41, 128, 185)),
    ("刘洋", 33, (192, 57, 43)),
]
for name, age, color in BOSSES:
    rel = "boss/%s.png" % name
    if not models.Boss.objects.filter(name=name).exists():
        make_image(os.path.join(settings.MEDIA_ROOT, rel), name[0], color)
        models.Boss.objects.create(name=name, age=age, img=rel)

# ---------------- 头像（XX，含预览图） ----------------
XXS = [
    ("产品经理", (233, 30, 99)),
    ("前端工程师", (0, 150, 136)),
    ("后端工程师", (63, 81, 181)),
    ("测试工程师", (255, 152, 0)),
    ("运维工程师", (96, 125, 139)),
    ("数据分析师", (121, 85, 72)),
]
for title, color in XXS:
    rel = "avatar/%s.png" % title
    if not models.XX.objects.filter(title=title).exists():
        make_image(os.path.join(settings.MEDIA_ROOT, rel), title[0], color)
        models.XX.objects.create(title=title, image=rel)

# ---------------- 订单（Order，混合状态/管理员） ----------------
ORDERS = [
    ("人体工学办公椅", 599, 2, 1),
    ("商务笔记本电脑", 6299, 2, 1),
    ("激光打印机", 1899, 1, 1),
    ("A4复印纸(整箱)", 159, 2, 7),
    ("高清投影仪", 3299, 1, 1),
    ("员工工牌(50个)", 240, 2, 7),
    ("立式饮水机", 459, 1, 7),
]
base = datetime.now().strftime("%Y%m%d%H%M")
for i, (title, price, status, admin_id) in enumerate(ORDERS, start=1):
    if not models.Order.objects.filter(title=title).exists():
        oid = "%s%02d%04d" % (base, i, 1000 + i)
        models.Order.objects.create(oid=oid, title=title, price=price,
                                    status=status, admin_id=admin_id)

print("=== 填充完成，当前数据量 ===")
print("Order:", models.Order.objects.count())
print("Boss:", models.Boss.objects.count())
print("City:", models.City.objects.count())
print("XX:", models.XX.objects.count())
