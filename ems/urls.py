from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # path('admin/', admin.site.urls),  # 已注释，使用自己的管理员管理
    path('', include('app01.urls')),
]

# 开发环境：让 /media/ 下的上传文件可以被访问
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
