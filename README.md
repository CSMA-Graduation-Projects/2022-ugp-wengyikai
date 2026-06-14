# UserStoryLLM

一个基于 FastAPI + Vue 2 的智能用户故事生成系统。当前仓库已修复以下影响运行和部署的问题：

- 后端依赖文件中的错误启动命令已移除，`backend/requirements.txt` 现在可以直接安装。
- 前端不再硬编码 `127.0.0.1:8000`，默认通过 `/api` 访问后端，并支持使用环境变量覆盖。
- 开发环境已补充代理配置，前端本地联调时无需改源码。

## 运行环境

- Python 3.10 及以上
- Node.js 18 或 20 LTS
- npm 9 及以上
- Docker Desktop 4.0 及以上（可选，用于一键部署）

> 说明：在 Node.js 24 下也可以安装和构建，但会出现引擎版本警告。答辩或部署建议使用 LTS 版本，避免不必要的不兼容风险。

## Docker / Nginx 一键部署

仓库根目录已经补齐以下部署文件：

- `docker-compose.yml`：一键启动前后端。
- `backend/Dockerfile`：FastAPI 后端镜像。
- `frontend/Dockerfile`：Vue 构建 + Nginx 静态服务镜像。
- `frontend/nginx.conf`：负责前端静态资源和 `/api` 反向代理。

推荐流程：

```powershell
Copy-Item .env.example .env
docker compose up -d --build
```

启动完成后访问：

- 前端页面：`http://127.0.0.1:8080`
- 后端健康检查（经 Nginx 代理）：`http://127.0.0.1:8080/api/health`

如需真实调用大模型，请先在根目录 `.env` 中设置：

```env
DEEPSEEK_API_KEY=your_real_key
DATABASE_URL=sqlite:////app/storage/user_story_kb.db
APP_PORT=8080
```

说明：

- SQLite 数据库存放在 Docker 卷 `backend-storage` 中，重建容器不会丢失数据库。
- 内置知识库文件仍保留在镜像内，不会被持久化卷覆盖。
- 前端容器内置 Nginx，会将 `/api/*` 自动转发给后端容器 `backend:8000`。

常用命令：

```powershell
docker compose logs -f
docker compose down
docker compose down -v
```

如果答辩现场网络受限，可以提前在本机完成镜像构建；现场只需要执行：

```powershell
docker compose up -d
```

## 后端启动

进入 `backend` 目录后执行：

```powershell
python -m pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

健康检查：

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

首次使用时请参考 `backend/.env.example` 配置环境变量，再补齐 `backend/.env`。如果没有配置 `DEEPSEEK_API_KEY`，健康检查和知识库接口仍可启动，但依赖大模型的生成接口会返回错误提示。

## 前端启动

进入 `frontend` 目录后执行：

```powershell
npm install
npm run serve
```

构建生产包：

```powershell
npm run build
```

前端默认通过 `/api` 调用后端；开发环境会由 `frontend/vue.config.js` 自动代理到 `http://127.0.0.1:8000`。

如果你的部署环境不是同域反向代理，可以在 `frontend/.env.example` 的基础上创建自己的环境文件，例如：

```env
VUE_APP_API_BASE_URL=http://your-api-host:8000
```

## 本地联调与答辩演示

推荐使用下面这组命令进行本地演示：

```powershell
# 终端 1
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 终端 2
cd frontend
npm run serve
```

这样浏览器访问前端开发服务器时，所有 `/api/*` 请求都会自动转发到本地后端。即使答辩现场无法访问云环境，也可以完整演示一次需求生成流程。

## 生产部署建议

生产环境建议将前端静态资源和后端 API 放到同一域名下，并通过 Nginx 反向代理 `/api`：

```nginx
server {
    listen 80;
    server_name your-domain;

    location / {
        root /srv/userstoryllm/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 接口示例

健康检查接口：

```http
GET /health
```

典型需求生成接口：

```http
POST /generate_and_evaluate
Content-Type: application/json

{
  "requirement": "用户可以注册登录系统，并查看和修改个人资料。"
}
```

响应结构示例：

```json
{
  "success": true,
  "message": "操作成功",
  "data": {
    "knowledge_context": "...",
    "result": {
      "structured_requirement": {
        "roles": ["用户"],
        "actions": ["注册", "登录", "查看个人资料", "修改个人资料"],
        "conditions": [],
        "goals": ["完成账户管理"]
      },
      "user_stories": ["作为用户，我希望能够注册并登录系统，以便管理个人资料。"],
      "tasks": []
    },
    "evaluation": {
      "completeness": 0,
      "clarity": 0,
      "consistency": 0,
      "overall_score": 0,
      "suggestions": []
    }
  }
}
```

## 已完成验证

- 后端：`python -m pip install -r requirements.txt` 安装成功。
- 后端：`python -c "from main import app; print(app.title)"` 导入成功。
- 前端：`npm install` 成功。
- 前端：`npm run build` 成功生成 `frontend/dist`。

## 论文实验材料

仓库已经补充论文支撑所需的实验资产：

- `backend/data/experiment_samples.json`：主实验样本。
- `backend/data/failure_cases.json`：失败与异常输入样本。
- `backend/task_tests.py`：单元测试、接口校验、失败案例和本地性能检查。
- `backend/experiment_runner.py`：生成三组对比、显著性统计、性能测试和人工评审模板。
- `论文实验与测试补充说明.md`：可直接对应论文第4章、第5章、第6章的补写说明。

常用命令：

```powershell
cd backend
python task_tests.py
python experiment_runner.py --sample-limit 12 --performance-sample-count 2 --repeats 3 --concurrency-levels 1 2
```