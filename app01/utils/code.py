import os
import random
from PIL import Image, ImageDraw, ImageFont


def check_code(width=120, height=35, char_length=4, font_file=None, font_size=28):
    """生成随机验证码图片和对应的字符串"""
    code = []
    img = Image.new(mode='RGB', size=(width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img, mode='RGB')

    def rnd_char():
        """随机大写字母"""
        return chr(random.randint(65, 90))

    def char_color():
        """字符用深色，保证在白底上对比度高、看得清"""
        return random.randint(0, 90), random.randint(0, 90), random.randint(60, 150)

    def noise_color():
        """干扰用偏亮的颜色，避免压过字符"""
        return random.randint(120, 230), random.randint(120, 230), random.randint(120, 230)

    # 选择字体：外部指定优先，其次 Windows 系统字体，最后才用内置小字体
    if font_file:
        font = ImageFont.truetype(font_file, font_size)
    else:
        candidates = [
            r"C:\Windows\Fonts\consola.ttf",
            r"C:\Windows\Fonts\arial.ttf",
        ]
        sys_font = next((f for f in candidates if os.path.exists(f)), None)
        if sys_font:
            font = ImageFont.truetype(sys_font, font_size)
        else:
            font = ImageFont.load_default()

    # 写文字
    for i in range(char_length):
        char = rnd_char()
        code.append(char)
        h = random.randint(0, 4)
        draw.text((i * width / char_length, h), char, fill=char_color(), font=font)

    # 画干扰点
    for _ in range(40):
        draw.point([random.randint(0, width), random.randint(0, height)], fill=noise_color())

    # 画干扰线
    for _ in range(4):
        draw.line((random.randint(0, width), random.randint(0, height),
                   random.randint(0, width), random.randint(0, height)), fill=noise_color())

    return img, ''.join(code)
