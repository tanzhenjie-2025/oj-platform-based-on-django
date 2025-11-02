FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt /app/

# 修复这一行 - 正确的语法
RUN apt-get update && apt-get install -y --no-install-recommends \
    pkg-config \
    libmariadb-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/

COPY . /app/

EXPOSE 8000

CMD ["gunicorn", "CheckObjection.wsgi:application", "--bind", "0.0.0.0:8000"]