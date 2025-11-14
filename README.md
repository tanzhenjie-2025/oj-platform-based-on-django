# OJ Platform: 基于Django的在线判题系统

一款面向编程教学、算法竞赛的轻量级在线判题平台，支持代码在线提交、实时判题反馈、比赛管理、用户权限控制等核心功能，基于Django + Celery + Channels 技术栈构建，架构清晰、部署灵活。

## 核心功能

- **题目管理**：支持题目发布、编辑、分类标签，包含题目描述、输入输出样例、测试用例管理
- **在线判题**：多语言支持（Python/Java/C++），实时代码提交、异步判题，返回AC/WA/TLE/MLE等结果
- **比赛模块**：支持创建编程比赛（OI/ACM模式）、比赛排名实时更新、提交记录追溯
- **用户系统**：注册/登录、个人提交记录、AC题目统计、比赛成绩归档
- **实时交互**：基于WebSocket的判题状态推送，无需手动刷新页面（没实现
- **后台管理**：通过Django Admin快速管理题目、用户、比赛数据，支持数据导出
- **容器化部署**：支持Docker一键部署，适配开发/生产环境

## 技术栈

| 模块         | 技术选型                          |
|--------------|-----------------------------------|
| 核心框架     | Django 4.2 + Django REST Framework |
| 异步任务     | Celery（判题任务调度）            |
| 实时通信     | Channels（WebSocket支持）         |
| 数据库       | SQLite（开发）/ MySQL（生产）     |
| 判题核心     | 自定义代码沙箱（安全隔离）        |
| 部署工具     | Docker + Docker Compose           |
| 自动化构建   | Jenkins（可选）                   |

## 环境要求

- Python 3.9+
- 操作系统：Linux/macOS/Windows（推荐Linux生产环境）(ubuntu24用不了judge0环境不兼容，亲测ubuntu20可以)
- 可选：Docker 20.10+（容器化部署）
- 可选：Redis（Celery Broker + 缓存，推荐生产环境使用）

## 快速开始

### 方式1：本地开发环境部署

1. 克隆仓库
```bash
git clone https://github.com/tanzhenjie-2025/oj-platform-based-on-django.git
cd oj-platform-based-on-django
```

2. 安装依赖
```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate  # Windows

# 安装依赖包
pip install -r requirements.txt
```

3. 配置项目
```bash
# 复制配置文件（可选，自定义数据库、Redis等）
自己配.env文件就能跑
cp CheckObjection/settings.py CheckObjection/settings_local.py
# 编辑settings_local.py修改配置（如数据库连接、Redis地址）
```

4. 数据库迁移
```bash
python manage.py makemigrations
python manage.py migrate
```

5. 创建超级管理员（后台管理）
```bash
python manage.py createsuperuser
# 按照提示输入用户名、邮箱、密码
```

6. 启动服务
```bash
# 启动Django开发服务器
python manage.py runserver

# 启动Celery（异步判题任务，需新开终端）
celery -A mycelery.main worker --loglevel=info

# 启动Channels（WebSocket，需新开终端）
daphne CheckObjection.asgi:application

#一般是这样启动的
docker-compose up -d 
```

7. 访问系统
- 前台：http://127.0.0.1:8000
- 后台管理：http://127.0.0.1:8000/admin

### 方式2：Docker一键部署

1. 确保已安装Docker和Docker Compose
2. 启动服务
```bash
git clone https://github.com/tanzhenjie-2025/oj-platform-based-on-django.git
cd oj-platform-based-on-django
docker-compose up -d
```
3. 初始化管理员账号
```bash
docker-compose exec web python manage.py createsuperuser
```
4. 访问系统：http://服务器IP:8000（默认端口8000，可在docker-compose.yml修改）

## 项目目录结构（核心）

```
oj-platform-based-on-django/
├── CheckObjection/          # 项目核心配置（URL、数据库、中间件等）
├── CheckObjectionApp/       # 核心业务应用（题目、判题、比赛、用户模块）
│   ├── models.py            # 数据模型（题目、用户、提交记录、比赛等）
│   ├── views.py            # 视图逻辑（接口、页面渲染）
│   ├── code.py              # 判题核心逻辑（代码编译、运行、结果校验）
│   ├── consumers.py         # WebSocket实时通信（判题状态推送）
│   └── templates/           # 前端页面模板
├── mycelery/                # Celery异步任务配置（判题任务调度）
├── manage.py                # Django项目管理脚本
└── requirements.txt         # 项目依赖清单
```

## 使用说明

### 1. 后台管理操作
1. 登录后台管理系统（/admin）
2. 先添加「题目分类」「测试用例」
3. 发布题目时关联测试用例，设置时间限制、内存限制
4. 创建比赛并关联题目，设置比赛开始/结束时间

### 2. 普通用户操作
1. 注册账号并登录
2. 在「题目列表」选择题目，查看描述后提交代码
3. 提交后可在「提交记录」查看判题结果（AC/WA/TLE等）
4. 比赛期间进入「比赛专区」，提交代码后实时更新排名

## 注意事项
1. 生产环境建议使用MySQL数据库，替换默认的SQLite
2. 判题功能依赖系统环境，Linux服务器需安装对应编程语言编译器（如g++、openjdk）
3. 建议配置Redis作为Celery Broker，提升异步任务调度效率
4. 代码沙箱存在安全风险，生产环境需限制代码运行权限（如使用Docker隔离）

## 贡献指南
1. Fork本仓库
2. 创建feature分支（`git checkout -b feature/xxx`）
3. 提交代码（`git commit -m "add xxx feature"`）
4. 推送分支（`git push origin feature/xxx`）
5. 提交Pull Request

## 许可证
本项目基于MIT许可证开源，详见 [LICENSE](LICENSE) 文件。

---

如需扩展功能（如多语言判题支持、更复杂的比赛规则）或解决部署问题，可提交Issue或联系开发者。