# Docker 与部署详解（面试版）

> 基于 price_monitor 项目的 Docker 实践，深入讲解面试必考知识点

---

## 目录

1. [Docker 核心概念](#1-docker-核心概念)
2. [Dockerfile 详解](#2-dockerfile-详解)
3. [Docker Compose 详解](#3-docker-compose-详解)
4. [Docker 网络与数据卷](#4-docker-网络与数据卷)
5. [Docker 常用命令](#5-docker-常用命令)
6. [部署最佳实践](#6-部署最佳实践)
7. [常见面试问题](#7-常见面试问题)
8. [总结与建议](#8-总结与建议)

---

## 1. Docker 核心概念

### 1.1 什么是 Docker？

**Docker** 是一个开源的容器化平台，用于开发、交付和运行应用程序。

**核心思想**：
- 将应用及其依赖打包到容器中
- 容器可以在任何环境中运行
- "一次构建，到处运行"（Build once, run anywhere）

### 1.2 为什么使用 Docker？

**传统部署的问题**：
```
开发环境：Python 3.11 + PostgreSQL 15
测试环境：Python 3.10 + PostgreSQL 14
生产环境：Python 3.9 + PostgreSQL 13

结果：在我的机器上能跑！（It works on my machine!）
```

**Docker 的解决方案**：
```
所有环境：Docker 容器（统一环境）
结果：在任何地方都能跑！
```

**优势**：
1. **环境一致性** - 开发、测试、生产环境完全一致
2. **快速部署** - 秒级启动，比虚拟机快得多
3. **资源隔离** - 每个容器独立运行，互不影响
4. **易于扩展** - 轻松启动多个容器实例
5. **版本控制** - 镜像可以版本化管理

### 1.3 Docker 三大核心概念

#### 1. 镜像（Image）

**定义**：只读的模板，包含运行应用所需的一切。

**类比**：镜像就像"类"（Class）

```python
# 镜像就像类定义
class PythonApp:
    def __init__(self):
        self.python_version = "3.11"
        self.dependencies = ["fastapi", "sqlmodel"]
```

**特点**：
- 只读，不可修改
- 分层存储（每个指令创建一层）
- 可以共享和复用

**你的项目镜像**：
```bash
# 基于 python:3.11-slim 镜像
# 添加依赖和应用代码
# 最终生成 price_monitor 镜像
```

#### 2. 容器（Container）

**定义**：镜像的运行实例，可以启动、停止、删除。

**类比**：容器就像"对象"（Object）

```python
# 容器就像类的实例
app1 = PythonApp()  # 容器 1
app2 = PythonApp()  # 容器 2
```

**特点**：
- 可读写
- 独立运行
- 可以创建、启动、停止、删除
- 容器之间相互隔离

**你的项目容器**：
```bash
# 从 price_monitor 镜像创建容器
docker run -d -p 8000:8000 price_monitor

# 可以创建多个容器
docker run -d -p 8001:8000 price_monitor  # 容器 1
docker run -d -p 8002:8000 price_monitor  # 容器 2
```

#### 3. 仓库（Repository）

**定义**：存储和分发镜像的地方。

**常见仓库**：
- **Docker Hub** - 官方公共仓库
- **阿里云容器镜像服务** - 国内镜像加速
- **私有仓库** - 公司内部使用

**类比**：
```
镜像仓库 = GitHub
镜像 = 代码仓库
```

### 1.4 Docker vs 虚拟机

| 特性 | Docker 容器 | 虚拟机 |
|------|------------|--------|
| 启动速度 | 秒级 | 分钟级 |
| 资源占用 | 少（MB 级别）| 多（GB 级别）|
| 性能 | 接近原生 | 有性能损耗 |
| 隔离性 | 进程级别 | 操作系统级别 |
| 系统支持 | 数千个容器 | 几十个虚拟机 |

**架构对比**：

```
虚拟机架构：
┌─────────────────────────────────┐
│   App A   │   App B   │   App C │
├───────────┼───────────┼─────────┤
│  Guest OS │  Guest OS │ Guest OS│
├───────────┴───────────┴─────────┤
│         Hypervisor              │
├─────────────────────────────────┤
│          Host OS                │
├─────────────────────────────────┤
│         Hardware                │
└─────────────────────────────────┘

Docker 架构：
┌─────────────────────────────────┐
│   App A   │   App B   │   App C │
├───────────┼───────────┼─────────┤
│        Docker Engine            │
├─────────────────────────────────┤
│          Host OS                │
├─────────────────────────────────┤
│         Hardware                │
└─────────────────────────────────┘
```

**面试要点**：
- Docker 容器共享宿主机内核，虚拟机有独立内核
- Docker 更轻量，虚拟机隔离性更强
- Docker 适合微服务，虚拟机适合需要完全隔离的场景

---

## 2. Dockerfile 详解

### 2.1 什么是 Dockerfile？

**Dockerfile** 是一个文本文件，包含构建 Docker 镜像的指令。

**你的项目 Dockerfile**：
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖（用于编译 Python 包）
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY app ./app

EXPOSE 8000
ENV PYTHONUNBUFFERED=1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2.2 Dockerfile 指令详解

#### FROM - 指定基础镜像

```dockerfile
FROM python:3.11-slim
```

**说明**：
- 每个 Dockerfile 必须以 FROM 开始
- `python:3.11-slim` 是官方 Python 镜像的精简版
- `slim` 版本比标准版小很多（约 120MB vs 900MB）

**面试要点**：
```
Q: 为什么选择 slim 版本？
A: 1. 镜像更小，下载和部署更快
   2. 减少攻击面，更安全
   3. 包含运行 Python 所需的基本工具

Q: 什么时候不用 slim？
A: 需要编译复杂 C 扩展时，可能需要标准版或 alpine 版
```

#### WORKDIR - 设置工作目录

```dockerfile
WORKDIR /app
```

**说明**：
- 设置容器内的工作目录
- 后续的 RUN、CMD、COPY 等指令都在这个目录下执行
- 如果目录不存在，会自动创建

**等价于**：
```bash
cd /app
```

#### RUN - 执行命令

```dockerfile
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*
```

**说明**：
- 在镜像构建时执行命令
- 每个 RUN 指令创建一个新的镜像层
- 多个命令用 `&&` 连接，减少镜像层数

**最佳实践**：
```dockerfile
# ❌ 不好：创建 3 个镜像层
RUN apt-get update
RUN apt-get install -y gcc
RUN rm -rf /var/lib/apt/lists/*

# ✅ 好：只创建 1 个镜像层
RUN apt-get update && apt-get install -y gcc \
    && rm -rf /var/lib/apt/lists/*
```

**面试要点**：
```
Q: 为什么要删除 /var/lib/apt/lists/*？
A: 清理 apt 缓存，减小镜像体积

Q: 为什么用 && 连接命令？
A: 减少镜像层数，减小镜像体积
```

#### COPY - 复制文件

```dockerfile
COPY requirements.txt .
COPY app ./app
```

**说明**：
- 从宿主机复制文件到容器
- `.` 表示当前工作目录（/app）

**COPY vs ADD**：
```dockerfile
# COPY：只复制文件
COPY requirements.txt .

# ADD：可以复制 URL，自动解压 tar
ADD https://example.com/file.tar.gz .  # 下载并解压
```

**面试高频问题**：
```
Q: COPY 和 ADD 的区别？
A: COPY：只复制文件，推荐使用
   ADD：可以下载 URL 和自动解压，功能更多但不透明

   最佳实践：优先使用 COPY，除非需要 ADD 的特殊功能
```

#### RUN pip install - 安装依赖

```dockerfile
RUN pip install --no-cache-dir -r requirements.txt
```

**说明**：
- `--no-cache-dir`：不缓存下载的包，减小镜像体积
- 先 COPY requirements.txt，再安装依赖（利用缓存）

**Docker 构建缓存**：
```dockerfile
# ✅ 好：利用缓存
COPY requirements.txt .           # 只有 requirements.txt 变化时才重新执行
RUN pip install -r requirements.txt
COPY app ./app                    # 代码变化不影响依赖安装

# ❌ 不好：每次代码变化都重新安装依赖
COPY . .
RUN pip install -r requirements.txt
```

#### EXPOSE - 声明端口

```dockerfile
EXPOSE 8000
```

**说明**：
- 声明容器监听的端口
- 仅用于文档说明，不会实际映射端口
- 实际映射需要 `docker run -p`

**面试要点**：
```
Q: EXPOSE 和 -p 的区别？
A: EXPOSE：声明端口（文档作用）
   -p：实际映射端口

   docker run -p 8000:8000 image  # 必须用 -p 才能访问
```

#### ENV - 设置环境变量

```dockerfile
ENV PYTHONUNBUFFERED=1
```

**说明**：
- 设置环境变量
- `PYTHONUNBUFFERED=1`：Python 输出不缓冲，实时显示日志

**常用环境变量**：
```dockerfile
ENV PYTHONUNBUFFERED=1          # Python 不缓冲输出
ENV PYTHONDONTWRITEBYTECODE=1   # 不生成 .pyc 文件
ENV DATABASE_URL=postgresql://...
```

#### CMD - 容器启动命令

```dockerfile
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**说明**：
- 容器启动时执行的命令
- 一个 Dockerfile 只能有一个 CMD
- 可以被 `docker run` 命令覆盖

**CMD vs ENTRYPOINT**：
```dockerfile
# CMD：可以被覆盖
CMD ["uvicorn", "app.main:app"]
# docker run image python script.py  # 覆盖 CMD

# ENTRYPOINT：不能被覆盖（除非用 --entrypoint）
ENTRYPOINT ["uvicorn"]
CMD ["app.main:app"]  # 作为 ENTRYPOINT 的参数
# docker run image app.other:app  # 只覆盖 CMD
```

**面试高频问题**：
```
Q: CMD 和 ENTRYPOINT 的区别？
A: CMD：容器启动命令，可以被 docker run 覆盖
   ENTRYPOINT：容器入口点，不容易被覆盖

   组合使用：
   ENTRYPOINT ["uvicorn"]
   CMD ["app.main:app", "--host", "0.0.0.0"]

   这样 uvicorn 固定，但可以覆盖参数
```

### 2.3 Dockerfile 最佳实践

#### 1. 利用构建缓存

```dockerfile
# ✅ 好：先复制依赖文件，再复制代码
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY app ./app

# ❌ 不好：代码变化导致重新安装依赖
COPY . .
RUN pip install -r requirements.txt
```

#### 2. 减少镜像层数

```dockerfile
# ✅ 好：合并命令
RUN apt-get update && apt-get install -y gcc \
    && rm -rf /var/lib/apt/lists/*

# ❌ 不好：多个 RUN
RUN apt-get update
RUN apt-get install -y gcc
RUN rm -rf /var/lib/apt/lists/*
```

#### 3. 使用 .dockerignore

```
# .dockerignore
__pycache__/
*.pyc
.git/
.venv/
*.md
.env
```

**作用**：
- 类似 .gitignore
- 排除不需要的文件，减小构建上下文
- 加快构建速度

#### 4. 多阶段构建（高级）

```dockerfile
# 阶段 1：构建
FROM python:3.11 AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# 阶段 2：运行
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY app ./app
CMD ["python", "app/main.py"]
```

**优势**：
- 最终镜像不包含构建工具
- 镜像更小，更安全

---
## 3. Docker Compose 详解

### 3.1 什么是 Docker Compose？

**Docker Compose** 是用于定义和运行多容器 Docker 应用的工具。

**为什么需要 Docker Compose？**

**单容器场景**：
```bash
# 手动启动每个容器
docker run -d --name db postgres:15
docker run -d --name redis redis:alpine
docker run -d --name web -p 8000:8000 myapp
```

**问题**：
- 命令太长，容易出错
- 容器之间的依赖关系不清晰
- 难以管理和维护

**Docker Compose 解决方案**：
```yaml
# docker-compose.yml
services:
  web:
    build: .
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis
  
  db:
    image: postgres:15
  
  redis:
    image: redis:alpine
```

```bash
# 一条命令启动全部已定义服务
# 当前更推荐先迁移、再按需启动具体服务
# 如确实需要一次性启动全部服务，可使用：
docker compose up -d
```

### 3.2 你的项目 docker-compose.yml 详解

> 当前仓库实际运行策略已经调整为“迁移优先”，并且 `web` 服务代码挂载目录已修正为 `/app`，下面示例与说明按当前实际状态展开。

```yaml
services:
  web:
    build: .
    container_name: monitor_web
    restart: always
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://admin:mypassword@db/monitor_db
      - REDIS_URL=redis://redis:6379
      - DB_INIT_MODE=migrate_only
    volumes:
      - .:/app
    depends_on:
      db:
        condition: service_healthy

  db:
    image: postgres:15-alpine
    container_name: monitor_db
    restart: always
    environment:
      - POSTGRES_USER=admin
      - POSTGRES_PASSWORD=mypassword
      - POSTGRES_DB=monitor_db
    ports:
      - "5432:5432"
    volumes:
      - pg_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U admin -d monitor_db"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:alpine
    container_name: monitor_redis
    restart: always
    ports:
      - "6379:6379"

volumes:
  pg_data:
```

### 3.3 Docker Compose 配置详解

#### services - 定义服务

```yaml
services:
  web:      # 服务名称
  db:       # 服务名称
  redis:    # 服务名称
```

**说明**：
- 每个服务对应一个容器
- 服务名称可以作为网络中的主机名

#### build - 构建镜像

```yaml
web:
  build: .              # 从当前目录的 Dockerfile 构建
  # 或
  build:
    context: .
    dockerfile: Dockerfile
```

#### image - 使用镜像

```yaml
db:
  image: postgres:15-alpine    # 使用官方镜像
```

#### container_name - 容器名称

```yaml
web:
  container_name: monitor_web
```

**说明**：
- 指定容器名称
- 不指定则自动生成（如 project_web_1）

#### restart - 重启策略

```yaml
web:
  restart: always
```

**重启策略**：
- no：不自动重启（默认）
- always：总是重启
- on-failure：失败时重启
- unless-stopped：除非手动停止，否则重启

**面试要点**：
```
Q: 什么时候用 always？
A: 生产环境，希望容器崩溃后自动重启

Q: always 和 unless-stopped 的区别？
A: always：Docker 重启后也会启动容器
   unless-stopped：Docker 重启后不会启动已停止的容器
```

#### command - 覆盖启动命令

```yaml
web:
  command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**说明**：
- 覆盖 Dockerfile 中的 CMD
- --reload：开发模式，代码变化自动重启

#### ports - 端口映射

```yaml
web:
  ports:
    - "8000:8000"    # 宿主机:容器
    - "8001:8000"    # 多个映射
```

**格式**：
```yaml
ports:
  - "宿主机端口:容器端口"
  - "8000:8000"      # 映射到 8000
  - "8001:8000"      # 映射到 8001
```

#### environment - 环境变量

```yaml
web:
  environment:
    - DATABASE_URL=postgresql+asyncpg://admin:mypassword@db/monitor_db
    - REDIS_URL=redis://redis:6379
    - DB_INIT_MODE=migrate_only
```

**注意**：
- `db` 和 `redis` 是服务名，容器之间通过服务名通信
- `DB_INIT_MODE=migrate_only` 表示应用启动时不自动执行 `create_all`
- 当前推荐流程是先执行 `alembic upgrade head`，再启动 `web`

**面试要点**：
```
Q: 为什么 DATABASE_URL 中用 @db 而不是 @localhost？
A: Docker Compose 自动创建网络
   服务名（db）可以作为主机名
   容器之间通过服务名通信
```

#### volumes - 数据卷

```yaml
web:
  volumes:
    - .:/app               # 挂载当前目录到容器 /app

db:
  volumes:
    - pg_data:/var/lib/postgresql/data    # 命名卷

volumes:
  pg_data:                 # 声明命名卷
```

**数据卷类型**：

1. **绑定挂载（Bind Mount）**：
```yaml
volumes:
  - ./app:/app           # 宿主机目录:容器目录
```
- 用于开发：代码变化实时同步

2. **命名卷（Named Volume）**：
```yaml
volumes:
  - pg_data:/var/lib/postgresql/data

volumes:
  pg_data:               # 声明
```
- 用于持久化数据
- 数据不会随容器删除而丢失

**面试要点**：
```
Q: 为什么数据库用命名卷，代码用绑定挂载？
A: 数据库：数据需要持久化，不能丢失
   代码：开发时需要实时同步

Q: 容器删除后，命名卷的数据会丢失吗？
A: 不会，命名卷独立于容器
   需要手动删除：docker volume rm pg_data
```

#### depends_on - 服务依赖

```yaml
web:
  depends_on:
    db:
      condition: service_healthy
```

**说明**：
- 控制服务启动顺序
- service_healthy：等待 db 健康检查通过

**依赖条件**：
- service_started：服务启动即可（默认）
- service_healthy：等待健康检查通过
- service_completed_successfully：等待服务成功退出

**面试要点**：
```
Q: depends_on 能保证服务完全启动吗？
A: 不能，只保证容器启动
   需要配合 healthcheck 确保服务就绪

Q: 为什么 web 依赖 db？
A: web 需要连接数据库
   如果 db 未启动，web 会连接失败
```

#### healthcheck - 健康检查

```yaml
db:
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U admin -d monitor_db"]
    interval: 5s
    timeout: 5s
    retries: 5
```

**说明**：
- test：健康检查命令
- interval：检查间隔
- timeout：超时时间
- retries：重试次数

**健康检查流程**：
```
1. 容器启动
2. 等待 5 秒（interval）
3. 执行 pg_isready 命令
4. 如果失败，等待 5 秒重试
5. 重试 5 次后仍失败，标记为 unhealthy
```

**面试要点**：
```
Q: 为什么需要健康检查？
A: 确保服务真正就绪
   容器启动 ≠ 服务就绪
   PostgreSQL 启动需要时间

Q: pg_isready 是什么？
A: PostgreSQL 自带的健康检查工具
   检查数据库是否可以接受连接
```

### 3.4 Docker Compose 常用命令

```bash
# 启动数据库和 Redis
docker compose up -d db redis

# 先执行数据库迁移
docker compose run --rm web alembic upgrade head

# 再启动后端服务
docker compose up -d web

# 如需完整启动全部服务
docker compose up -d

# 查看服务状态
docker compose ps

# 查看日志
docker compose logs -f web

# 停止所有服务
docker compose down

# 重启服务
docker compose restart web

# 进入容器
docker compose exec web bash

# 构建镜像
docker compose build

# 查看服务配置
docker compose config
```

**面试要点**：
```
Q: docker compose up 和 docker compose up -d 的区别？
A: up：前台运行，显示日志
   up -d：后台运行（detached）

Q: docker compose down 和 docker compose stop 的区别？
A: stop：停止容器，不删除
   down：停止并删除容器、网络（不删除卷）
```

---


## 4. Docker 网络与数据卷

### 4.1 Docker 网络

**Docker Compose 自动创建网络**：
```bash
# 查看网络
docker network ls

# 输出
NETWORK ID     NAME                    DRIVER
abc123         price_monitor_default   bridge
```

**网络特性**：
- 同一网络中的容器可以通过服务名通信
- 自动 DNS 解析

**示例**：
```yaml
# docker-compose.yml
services:
  web:
    environment:
      - DATABASE_URL=postgresql://admin:pass@db/monitor_db
      #                                    ↑
      #                              服务名作为主机名
  db:
    image: postgres:15
```

**网络类型**：
1. **bridge**（默认）：容器之间可以通信
2. **host**：容器使用宿主机网络
3. **none**：无网络

**自定义网络**：
```yaml
services:
  web:
    networks:
      - frontend
      - backend
  
  db:
    networks:
      - backend

networks:
  frontend:
  backend:
```

### 4.2 Docker 数据卷

**为什么需要数据卷？**

**问题**：
```bash
# 容器删除，数据丢失
docker run -d --name db postgres:15
docker rm -f db  # 数据库数据丢失！
```

**解决方案**：
```yaml
db:
  volumes:
    - pg_data:/var/lib/postgresql/data

volumes:
  pg_data:
```

**数据卷管理**：
```bash
# 查看数据卷
docker volume ls

# 查看数据卷详情
docker volume inspect pg_data

# 删除数据卷
docker volume rm pg_data

# 删除未使用的数据卷
docker volume prune
```

**面试要点**：
```
Q: 容器删除后，数据卷会自动删除吗？
A: 不会，需要手动删除
   docker-compose down -v  # 删除容器和卷

Q: 如何备份数据卷？
A: docker run --rm -v pg_data:/data -v $(pwd):/backup \
     ubuntu tar czf /backup/backup.tar.gz /data
```

---

## 5. Docker 常用命令

### 5.1 镜像相关

```bash
# 构建镜像
docker build -t price_monitor .

# 查看镜像
docker images

# 删除镜像
docker rmi price_monitor

# 拉取镜像
docker pull python:3.11

# 推送镜像
docker push myregistry/price_monitor

# 查看镜像历史
docker history price_monitor

# 导出镜像
docker save -o price_monitor.tar price_monitor

# 导入镜像
docker load -i price_monitor.tar

# 清理悬空镜像
docker image prune
```

### 5.2 容器相关

```bash
# 运行容器
docker run -d -p 8000:8000 --name web price_monitor

# 查看运行中的容器
docker ps

# 查看所有容器（包括停止的）
docker ps -a

# 停止容器
docker stop web

# 启动容器
docker start web

# 重启容器
docker restart web

# 删除容器
docker rm web

# 强制删除运行中的容器
docker rm -f web

# 查看容器日志
docker logs -f web

# 进入容器
docker exec -it web bash

# 查看容器详情
docker inspect web

# 查看容器资源使用
docker stats web

# 复制文件到容器
docker cp file.txt web:/app/

# 从容器复制文件
docker cp web:/app/file.txt .
```

### 5.3 系统清理

```bash
# 删除停止的容器
docker container prune

# 删除未使用的镜像
docker image prune

# 删除未使用的数据卷
docker volume prune

# 删除未使用的网络
docker network prune

# 清理所有未使用的资源
docker system prune -a
```

**面试要点**：
```
Q: docker run 和 docker start 的区别？
A: run：从镜像创建并启动新容器
   start：启动已存在的容器

Q: docker exec 和 docker attach 的区别？
A: exec：在容器中执行新命令（推荐）
   attach：附加到容器的主进程（退出会停止容器）

Q: -d 参数的作用？
A: detached 模式，后台运行容器
```

---

## 6. 部署最佳实践

### 6.1 开发环境 vs 生产环境

**开发环境**：
```yaml
# docker-compose.dev.yml
services:
  web:
    command: uvicorn app.main:app --reload  # 热重载
    volumes:
      - .:/app                              # 代码同步
    environment:
      - DEBUG=True
      - DB_INIT_MODE=migrate_only
```

**生产环境**：
```yaml
# docker-compose.prod.yml
services:
  web:
    command: uvicorn app.main:app --workers 4  # 多进程
    restart: always                             # 自动重启
    environment:
      - DEBUG=False
      - DB_INIT_MODE=migrate_only
```

**共同原则**：
- 无论开发还是生产，都优先执行 `alembic upgrade head`
- `DB_INIT_MODE=create_all` 仅作为空开发库临时兜底，不应作为正式部署常态

**使用不同配置**：
```bash
# 开发环境
docker compose -f docker-compose.yml -f docker-compose.dev.yml up

# 生产环境
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### 6.2 环境变量管理

**使用 .env 文件**：
```bash
# .env
POSTGRES_USER=admin
POSTGRES_PASSWORD=mypassword
DATABASE_URL=postgresql://admin:mypassword@db/monitor_db
DB_INIT_MODE=migrate_only
```

```yaml
# docker-compose.yml
services:
  db:
    environment:
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
```

**安全建议**：
- 不要将 .env 提交到 Git
- 生产环境使用密钥管理服务（如 AWS Secrets Manager）
- 使用 Docker Secrets（Swarm 模式）
- 对当前项目，默认不要在 `.env` 中把 `DB_INIT_MODE` 改成 `create_all`

### 6.3 日志管理

```yaml
services:
  web:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

**日志驱动**：
- `json-file`：默认，JSON 格式
- `syslog`：系统日志
- `journald`：systemd 日志
- `gelf`：Graylog
- `fluentd`：Fluentd

### 6.4 资源限制

```yaml
services:
  web:
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M
```

**说明**：
- `limits`：最大资源使用
- `reservations`：保证的最小资源

### 6.5 健康检查

```yaml
services:
  web:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

### 6.6 镜像优化

**1. 使用多阶段构建**：
```dockerfile
# 构建阶段
FROM python:3.11 AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# 运行阶段
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY app ./app
CMD ["python", "app/main.py"]
```

**2. 减少镜像层**：
```dockerfile
# ❌ 不好
RUN apt-get update
RUN apt-get install -y gcc
RUN rm -rf /var/lib/apt/lists/*

# ✅ 好
RUN apt-get update && apt-get install -y gcc \
    && rm -rf /var/lib/apt/lists/*
```

**3. 使用 .dockerignore**：
```
__pycache__/
*.pyc
.git/
.venv/
*.md
.env
```

**4. 选择合适的基础镜像**：
```dockerfile
# 标准版：~900MB
FROM python:3.11

# Slim 版：~120MB（推荐）
FROM python:3.11-slim

# Alpine 版：~50MB（可能有兼容性问题）
FROM python:3.11-alpine
```

---


## 7. 常见面试问题

### 7.1 Docker 基础问题

**Q1: 什么是 Docker？为什么使用 Docker？**
```
A: Docker 是容器化平台，用于打包、分发和运行应用

   优势：
   1. 环境一致性：开发、测试、生产环境完全一致
   2. 快速部署：秒级启动
   3. 资源隔离：容器之间互不影响
   4. 易于扩展：轻松启动多个实例
   5. 版本控制：镜像可以版本化
```

**Q2: Docker 和虚拟机的区别？**
```
A: Docker 容器：
   - 共享宿主机内核
   - 启动快（秒级）
   - 资源占用少（MB 级别）
   - 性能接近原生

   虚拟机：
   - 独立内核
   - 启动慢（分钟级）
   - 资源占用多（GB 级别）
   - 有性能损耗

   选择：
   - 微服务、快速部署 → Docker
   - 需要完全隔离、不同操作系统 → 虚拟机
```

**Q3: 镜像和容器的区别？**
```
A: 镜像（Image）：
   - 只读模板
   - 类似"类"（Class）
   - 包含应用和依赖

   容器（Container）：
   - 镜像的运行实例
   - 类似"对象"（Object）
   - 可读写，可以启动、停止、删除

   关系：
   镜像 → 容器（docker run）
   容器 → 镜像（docker commit）
```

### 7.2 Dockerfile 问题

**Q4: COPY 和 ADD 的区别？**
```
A: COPY：只复制文件（推荐）
   - COPY requirements.txt .

   ADD：功能更多
   - 可以下载 URL
   - 自动解压 tar 文件
   - ADD https://example.com/file.tar.gz .

   最佳实践：优先使用 COPY，除非需要 ADD 的特殊功能
```

**Q5: CMD 和 ENTRYPOINT 的区别？**
```
A: CMD：容器启动命令，可以被覆盖
   CMD ["uvicorn", "app.main:app"]
   docker run image python script.py  # 覆盖 CMD

   ENTRYPOINT：容器入口点，不容易被覆盖
   ENTRYPOINT ["uvicorn"]
   CMD ["app.main:app"]
   docker run image app.other:app  # 只覆盖 CMD

   组合使用：
   ENTRYPOINT 固定命令，CMD 提供默认参数
```

**Q6: RUN、CMD、ENTRYPOINT 的区别？**
```
A: RUN：构建时执行
   - 安装依赖、配置环境
   - 每个 RUN 创建一个镜像层

   CMD：容器启动时执行
   - 提供默认命令
   - 可以被 docker run 覆盖

   ENTRYPOINT：容器启动时执行
   - 作为容器的主命令
   - 不容易被覆盖
```

**Q7: 如何减小 Docker 镜像体积？**
```
A: 1. 使用精简基础镜像（slim、alpine）
   2. 多阶段构建
   3. 合并 RUN 指令
   4. 清理缓存和临时文件
   5. 使用 .dockerignore
   6. 只复制必要文件

   示例：
   RUN apt-get update && apt-get install -y gcc \
       && rm -rf /var/lib/apt/lists/*  # 清理缓存
```

### 7.3 Docker Compose 问题

**Q8: 什么是 Docker Compose？**
```
A: Docker Compose 是用于定义和运行多容器应用的工具

   优势：
   1. 一个文件定义所有服务
   2. 一条命令启动所有服务
   3. 管理服务依赖关系
   4. 自动创建网络

   使用场景：
   - 开发环境
   - 测试环境
   - 单机部署
```

**Q9: depends_on 能保证服务完全启动吗？**
```
A: 不能，只保证容器启动

   问题：
   - 容器启动 ≠ 服务就绪
   - PostgreSQL 启动需要时间

   解决方案：
   depends_on:
     db:
       condition: service_healthy  # 等待健康检查通过

   db:
     healthcheck:
       test: ["CMD", "pg_isready"]
```

**Q10: 为什么容器之间可以通过服务名通信？**
```
A: Docker Compose 自动创建网络

   机制：
   1. 创建默认网络（bridge）
   2. 所有服务加入该网络
   3. 自动 DNS 解析（服务名 → IP）

   示例：
   DATABASE_URL=postgresql://admin:pass@db/monitor_db
                                        ↑
                                   服务名作为主机名
```

### 7.4 网络与数据卷问题

**Q11: Docker 有哪些网络模式？**
```
A: 1. bridge（默认）：
      - 容器之间可以通信
      - 需要端口映射访问外部

   2. host：
      - 容器使用宿主机网络
      - 性能最好，但失去隔离性

   3. none：
      - 无网络
      - 完全隔离

   4. container：
      - 共享其他容器的网络
```

**Q12: 数据卷和绑定挂载的区别？**
```
A: 数据卷（Named Volume）：
   - Docker 管理
   - 持久化数据
   - 适合数据库

   绑定挂载（Bind Mount）：
   - 挂载宿主机目录
   - 实时同步
   - 适合开发环境

   示例：
   volumes:
     - pg_data:/var/lib/postgresql/data  # 数据卷
     - ./app:/app                        # 绑定挂载
```

**Q13: 容器删除后，数据卷会丢失吗？**
```
A: 不会，数据卷独立于容器

   删除容器：
   docker rm container  # 数据卷保留

   删除容器和卷：
   docker-compose down -v  # 同时删除卷

   手动删除卷：
   docker volume rm pg_data
```

### 7.5 项目相关问题

**Q14: 介绍一下你的项目 Docker 配置**
```
A: 我的项目使用 Docker Compose 编排 3 个服务：

   1. web（FastAPI 应用）：
      - 基于 python:3.11-slim
      - 端口映射 8000:8000
      - 挂载代码目录（开发模式）
      - 依赖 db 健康检查

   2. db（PostgreSQL）：
      - 使用 postgres:15-alpine
      - 数据持久化（命名卷）
      - 健康检查（pg_isready）

   3. redis（缓存）：
      - 使用 redis:alpine
      - 端口映射 6379:6379

   特点：
   - 服务依赖管理
   - 健康检查
   - 数据持久化
   - 自动重启
```

**Q15: 你的 Dockerfile 有什么优化？**
```
A: 1. 使用 slim 镜像：
      FROM python:3.11-slim  # 比标准版小 ~800MB

   2. 利用构建缓存：
      COPY requirements.txt .
      RUN pip install -r requirements.txt
      COPY app ./app  # 代码变化不影响依赖安装

   3. 清理缓存：
      RUN apt-get update && apt-get install -y gcc \
          && rm -rf /var/lib/apt/lists/*

   4. 设置环境变量：
      ENV PYTHONUNBUFFERED=1  # 实时显示日志

   5. 使用 .dockerignore：
      排除不必要的文件
```

**Q16: 如何部署你的项目？**
```
A: 开发环境：
   1. 克隆代码：git clone ...
   2. 启动基础服务：docker compose up -d db redis
   3. 执行迁移：docker compose run --rm web alembic upgrade head
   4. 启动应用：docker compose up -d web
   5. 查看日志：docker compose logs -f web
   6. 访问：http://localhost:8000

   生产环境：
   1. 构建镜像：docker build -t myapp:v1.0 .
   2. 推送镜像：docker push myregistry/myapp:v1.0
   3. 服务器拉取：docker pull myregistry/myapp:v1.0
   4. 启动服务：docker compose -f docker-compose.prod.yml up -d

   改进方向：
   - CI/CD 自动化部署
   - 使用 Kubernetes 编排
   - 添加监控和日志收集
```

**Q17: 遇到过什么 Docker 相关的问题？**
```
A: 1. 容器启动顺序问题：
      问题：web 启动时 db 未就绪
      解决：使用 depends_on + healthcheck

   2. 数据丢失问题：
      问题：容器删除后数据丢失
      解决：使用命名卷持久化数据

   3. 网络通信问题：
      问题：容器之间无法通信
      解决：确保在同一网络，使用服务名

   4. 镜像体积过大：
      问题：镜像 2GB+
      解决：使用 slim 镜像，多阶段构建
```

---

## 8. 总结与建议

### 8.1 Docker 知识清单

✅ **核心概念**
- [ ] 理解镜像、容器、仓库
- [ ] 理解 Docker vs 虚拟机
- [ ] 理解容器化的优势

✅ **Dockerfile**
- [ ] 掌握常用指令（FROM、RUN、COPY、CMD）
- [ ] 理解镜像分层
- [ ] 掌握构建缓存
- [ ] 掌握镜像优化技巧

✅ **Docker Compose**
- [ ] 掌握 docker-compose.yml 配置
- [ ] 理解服务依赖（depends_on）
- [ ] 理解健康检查（healthcheck）
- [ ] 掌握数据卷和网络

✅ **常用命令**
- [ ] 镜像管理（build、pull、push）
- [ ] 容器管理（run、start、stop、rm）
- [ ] 日志查看（logs）
- [ ] 进入容器（exec）

✅ **最佳实践**
- [ ] 开发/生产环境分离
- [ ] 环境变量管理
- [ ] 日志管理
- [ ] 资源限制
- [ ] 安全加固

### 8.2 你的项目优点

✅ **已经做得很好的地方**：
1. 使用 Docker Compose 编排多服务
2. 配置健康检查
3. 数据持久化（命名卷）
4. 服务依赖管理
5. 自动重启策略
6. 使用 slim 镜像

### 8.3 改进建议（面试加分项）

🔧 **可以改进的地方**：
1. 多阶段构建（减小镜像体积）
2. 添加 .dockerignore
3. 资源限制（CPU、内存）
4. 日志管理（限制日志大小）
5. 使用 secrets 管理敏感信息
6. 添加 CI/CD 自动化部署

### 8.4 面试准备建议

**准备讲述你的项目**：
```
1. 项目架构
   "我的项目使用 Docker Compose 编排 3 个服务：
    FastAPI 应用、PostgreSQL 数据库、Redis 缓存"

2. Docker 配置
   "使用 Dockerfile 构建应用镜像，
    使用 docker-compose.yml 编排服务"

3. 技术亮点
   "配置了健康检查确保服务就绪，
    使用命名卷持久化数据库数据，
    通过服务名实现容器间通信"

4. 遇到的挑战
   "最初遇到容器启动顺序问题，
    通过 depends_on + healthcheck 解决"

5. 部署流程
   "开发环境推荐流程：先 `docker compose up -d db redis`，
    再 `docker compose run --rm web alembic upgrade head`，
    最后 `docker compose up -d web`
    生产环境构建镜像并推送到镜像仓库"
```

### 8.5 学习资源

**官方文档**：
- [Docker 官方文档](https://docs.docker.com/)
- [Docker Compose 文档](https://docs.docker.com/compose/)
- [Dockerfile 最佳实践](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/)

**推荐阅读**：
- 《Docker 从入门到实践》
- 《Docker 容器与容器云》
- 《Kubernetes 权威指南》

**实践建议**：
1. 动手实践：自己搭建项目
2. 阅读优秀项目的 Dockerfile
3. 理解每个配置的作用
4. 尝试优化镜像体积
5. 学习 Kubernetes（进阶）

---

**祝你面试顺利！** 🎉

记住：
1. 理解 Docker 核心概念
2. 熟悉 Dockerfile 和 Docker Compose
3. 能够流畅讲解你的项目配置
4. 准备常见面试问题的答案
5. 强调实际项目经验

