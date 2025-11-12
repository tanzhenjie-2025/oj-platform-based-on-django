# run_dev.py - 开发环境专用
import uvicorn
import os

def main():
    # 设置Django环境变量，指向你的settings模块
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "CheckObjection.settings")
    uvicorn.run(
        "CheckObjection.asgi:application",  # 指向ASGI应用
        host="0.0.0.0",
        port=8000,
        log_level="debug",
        reload=True,  # 启用热重载 - 仅开发环境使用
        reload_dirs=["CheckObjection", "CheckObjectionApp"],  # 指定监视的目录
    )

if __name__ == "__main__":
    main()