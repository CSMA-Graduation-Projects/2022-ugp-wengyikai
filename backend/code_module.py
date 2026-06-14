# code_module.py
import os
import json
import time
from typing import Any, Dict, List

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)


def build_default_code_result(error_message: str = "") -> Dict[str, Any]:
    return {
        "project_structure": [],
        "frontend_code": "",
        "backend_code": "",
        "database_sql": "",
        "usage_notes": [],
        "error": error_message
    }


def build_code_prompt(requirement: str, story: str, tasks: List[Dict[str, Any]]) -> str:
    task_text = json.dumps(tasks, ensure_ascii=False, indent=2)

    return f"""
你是一位熟悉 Vue2、Element UI、FastAPI、SQLAlchemy 和 SQLite 的全栈开发工程师。
请根据原始需求、用户故事和任务拆解结果，生成该用户故事相关的代码骨架。

【重要要求】
1. 必须使用中文说明。
2. 必须只返回严格合法的 JSON 对象，不要输出 Markdown。
3. 生成的是“核心代码骨架”，不是完整项目。
4. 前端代码使用 Vue2 + Element UI。
5. 后端代码使用 FastAPI。
6. 数据库代码使用 SQLite/SQLAlchemy 或标准 SQL。
7. 代码中要包含适当中文注释。
8. 不要生成危险操作代码，例如删除系统文件、执行任意命令、暴露密钥等。
9. 如果某类代码与该用户故事关系不大，可以返回空字符串。

【原始需求】
{requirement}

【用户故事】
{story}

【相关任务】
{task_text}

【请严格返回以下 JSON 结构】
{{
  "project_structure": [
    "frontend/src/views/xxx.vue",
    "backend/api/xxx.py",
    "backend/models/xxx.py"
  ],
  "frontend_code": "Vue2 + Element UI 前端核心代码",
  "backend_code": "FastAPI 后端核心代码",
  "database_sql": "数据库建表或字段设计 SQL",
  "usage_notes": [
    "代码使用说明1",
    "代码使用说明2"
  ]
}}
"""


def normalize_code_result(result: Dict[str, Any]) -> Dict[str, Any]:
    project_structure = result.get("project_structure", [])
    usage_notes = result.get("usage_notes", [])

    if not isinstance(project_structure, list):
        project_structure = []

    if not isinstance(usage_notes, list):
        usage_notes = []

    return {
        "project_structure": [str(item) for item in project_structure],
        "frontend_code": str(result.get("frontend_code", "")).strip(),
        "backend_code": str(result.get("backend_code", "")).strip(),
        "database_sql": str(result.get("database_sql", "")).strip(),
        "usage_notes": [str(item) for item in usage_notes],
        "error": str(result.get("error", "")).strip()
    }


def classify_code_generation_error(error_message: str) -> str:
    text = str(error_message or "").strip()
    if not text:
        return ""
    if "DEEPSEEK_API_KEY" in text:
        return "missing_api_key"
    if "不是合法 JSON" in text:
        return "invalid_json"
    if "未生成有效代码内容" in text:
        return "empty_model_output"
    return "generation_error"


def generate_related_code_with_trace(requirement: str, story: str, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
    trace: Dict[str, Any] = {
        "prompt_story_length": len(str(story or "")),
        "task_count": len(tasks or []),
        "llm_called": False,
        "llm_inference_ms": 0.0,
        "error_type": "",
        "result_status": "error"
    }

    if not os.getenv("DEEPSEEK_API_KEY"):
        result = build_default_code_result("未检测到 DEEPSEEK_API_KEY，请检查 .env 配置")
        trace["error_type"] = classify_code_generation_error(result["error"])
        return {
            "result": result,
            "trace": trace
        }

    prompt = build_code_prompt(requirement, story, tasks)

    try:
        trace["llm_called"] = True
        llm_start = time.perf_counter()
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.2
        )
        trace["llm_inference_ms"] = round((time.perf_counter() - llm_start) * 1000, 2)

        content = response.choices[0].message.content
        parsed = json.loads(content)
        normalized = normalize_code_result(parsed)

        if not normalized["frontend_code"] and not normalized["backend_code"] and not normalized["database_sql"]:
            normalized["error"] = "模型未生成有效代码内容"

        trace["error_type"] = classify_code_generation_error(normalized.get("error", ""))
        trace["result_status"] = "error" if normalized.get("error") else "success"
        return {
            "result": normalized,
            "trace": trace
        }

    except json.JSONDecodeError:
        result = build_default_code_result("模型返回内容不是合法 JSON")
        trace["error_type"] = classify_code_generation_error(result["error"])
        return {
            "result": result,
            "trace": trace
        }
    except Exception as e:
        result = build_default_code_result(f"代码生成失败: {str(e)}")
        trace["error_type"] = classify_code_generation_error(result["error"])
        return {
            "result": result,
            "trace": trace
        }


def generate_related_code(requirement: str, story: str, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
    return generate_related_code_with_trace(requirement, story, tasks)["result"]