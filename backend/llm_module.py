# llm_module.py
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

VALID_TASK_TYPES = ["frontend", "backend", "database"]
GENERIC_RULE_TEMPLATE = """
【通用规则模板】
1. 优先提取角色、行为、条件、目标四类结构化信息。
2. 补充输入校验、权限控制、异常处理、状态流转、日志留痕和安全约束。
3. 将任务拆解为前端、后端、数据库三类，并给出真实 depends_on 依赖。
4. 对异常输入、重复提交、权限不足、数据不存在和并发冲突等失败场景给出显式任务。
""".strip()


def build_default_result(error_message: str = "") -> Dict[str, Any]:
    """
    构造默认返回结果。
    当模型调用失败、API Key 未配置或模型返回内容无法解析时，统一返回该结构，
    便于 main.py 和前端页面保持稳定处理。
    """
    return {
        "structured_requirement": {
            "roles": [],
            "actions": [],
            "conditions": [],
            "goals": []
        },
        "user_stories": [],
        "tasks": [],
        "error": error_message
    }


def safe_list(value: Any) -> List[Any]:
    """将模型返回字段安全转换为列表。"""
    return value if isinstance(value, list) else []


def normalize_task(task: Dict[str, Any], index: int) -> Dict[str, Any]:
    """规范化单个任务对象。"""
    task_id = str(task.get("id") or f"T{index + 1}").strip()
    name = str(task.get("name", "")).strip()
    task_type = str(task.get("type", "")).strip().lower()
    story = str(task.get("story", "")).strip()
    depends_on = task.get("depends_on", [])

    if task_type not in VALID_TASK_TYPES:
        task_type = "backend"

    if not isinstance(depends_on, list):
        depends_on = []

    normalized_depends_on = [
        str(item).strip()
        for item in depends_on
        if str(item).strip()
    ]

    return {
        "id": task_id or f"T{index + 1}",
        "name": name or f"任务{index + 1}",
        "type": task_type,
        "story": story,
        "depends_on": normalized_depends_on
    }


def normalize_result(result: Dict[str, Any]) -> Dict[str, Any]:
    """对大模型返回结果进行归一化处理。"""
    if not isinstance(result, dict):
        return build_default_result("模型返回结果不是 JSON 对象")

    structured = result.get("structured_requirement", {})
    if not isinstance(structured, dict):
        structured = {}

    normalized_structured = {
        "roles": [str(item).strip() for item in safe_list(structured.get("roles")) if str(item).strip()],
        "actions": [str(item).strip() for item in safe_list(structured.get("actions")) if str(item).strip()],
        "conditions": [str(item).strip() for item in safe_list(structured.get("conditions")) if str(item).strip()],
        "goals": [str(item).strip() for item in safe_list(structured.get("goals")) if str(item).strip()]
    }

    stories = result.get("user_stories", [])
    if not isinstance(stories, list):
        stories = []
    normalized_stories = [
        str(item).strip()
        for item in stories
        if str(item).strip()
    ]

    tasks = result.get("tasks", [])
    if not isinstance(tasks, list):
        tasks = []
    normalized_tasks = [
        normalize_task(task, index)
        for index, task in enumerate(tasks)
        if isinstance(task, dict)
    ]

    return {
        "structured_requirement": normalized_structured,
        "user_stories": normalized_stories,
        "tasks": normalized_tasks,
        "error": str(result.get("error", "")).strip()
    }


def build_prompt(requirement: str, context: str) -> str:
    """构造用户故事生成 Prompt。"""
    return f"""
你是一位资深的敏捷开发与需求工程专家。请根据输入内容完成需求解析、用户故事生成与任务拆解。

【输出要求】
1. 必须全程使用中文。
2. 必须只返回严格合法的 JSON 对象，不要输出任何解释文字、Markdown、注释。
3. 用户故事必须遵循模板：
   “作为[角色]，我想要[功能]，以便[价值]”
4. 任务必须体现真实依赖关系，字段 depends_on 存放的是前置任务 id 列表，而不是故事文本。
5. 若需求中包含多个业务模块，应尽量拆分为多条用户故事。
6. 请尽量结合知识增强上下文中的前置条件、异常场景、安全约束和典型任务。
7. 不要生成微型故事、小说化叙述或额外说明。

【知识增强上下文】
{context}

【原始需求】
{requirement}

【请严格返回以下 JSON 结构】
{{
  "structured_requirement": {{
    "roles": ["角色1", "角色2"],
    "actions": ["行为1", "行为2"],
    "conditions": ["条件1", "条件2"],
    "goals": ["目标1", "目标2"]
  }},
  "user_stories": [
    "作为用户，我想要使用账号密码登录系统，以便安全访问个人功能"
  ],
  "tasks": [
    {{
      "id": "T1",
      "name": "设计登录页面",
      "type": "frontend",
      "story": "作为用户，我想要使用账号密码登录系统，以便安全访问个人功能",
      "depends_on": []
    }},
    {{
      "id": "T2",
      "name": "设计用户表及密码字段",
      "type": "database",
      "story": "作为用户，我想要使用账号密码登录系统，以便安全访问个人功能",
      "depends_on": []
    }},
    {{
      "id": "T3",
      "name": "实现登录接口",
      "type": "backend",
      "story": "作为用户，我想要使用账号密码登录系统，以便安全访问个人功能",
      "depends_on": ["T1", "T2"]
    }}
  ]
}}

【额外约束】
1. structured_requirement 中必须尽量提取角色、行为、条件、目标。
2. tasks 中 type 只能取以下三类之一："frontend"、"backend"、"database"。
3. 每个任务必须有唯一 id，例如 T1、T2、T3。
4. 每条用户故事至少拆出 2 到 4 个任务。
5. 若需求中存在知识库命中的模块，请在任务拆解中体现相关要素，例如安全约束、异常场景、必要功能点。
6. 对于登录、注册、支付、订单、用户管理、权限管理、报表统计、审批流等常见模块，请优先结合知识上下文补全任务。
7. 任务名称应尽量具体，避免只写“实现功能”“开发模块”等笼统表述。
"""


def get_rule_template_context() -> str:
    return GENERIC_RULE_TEMPLATE


def classify_generation_error(error_message: str) -> str:
    text = str(error_message or "").strip()
    if not text:
        return ""
    if "DEEPSEEK_API_KEY" in text:
        return "missing_api_key"
    if "不能为空" in text:
        return "empty_requirement"
    if "不是合法 JSON" in text or "不是 JSON" in text:
        return "invalid_json"
    if "未生成有效" in text:
        return "empty_model_output"
    return "inference_error"


def extract_requirement_from_code(code: str) -> str:
    """
    从代码片段中提取自然语言需求描述。
    调用 LLM 进行分析，返回 1~3 句中文需求总结。
    """
    if not os.getenv("DEEPSEEK_API_KEY"):
        raise Exception("未配置 DEEPSEEK_API_KEY")

    prompt = f"""你是一位资深系统分析师，请阅读以下代码，并提炼出该代码所实现的核心业务功能需求描述。
请用 1~3 句自然语言中文概括，只输出描述文本，不要包含任何其他说明。

代码：{code}"""
    
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=200
    )
    return response.choices[0].message.content.strip()


def generate_structured_data_with_trace(
    requirement: str,
    context: str,
    strategy: str = "knowledge_enhanced"
) -> Dict[str, Any]:
    """返回生成结果及模型调用轨迹，便于实验和性能分析。"""
    trace: Dict[str, Any] = {
        "strategy": strategy,
        "prompt_chars": 0,
        "used_context": bool(str(context or "").strip()),
        "llm_called": False,
        "llm_inference_ms": 0.0,
        "story_count": 0,
        "task_count": 0,
        "error_type": "",
        "result_status": "error"
    }

    if not os.getenv("DEEPSEEK_API_KEY"):
        result = build_default_result("未检测到 DEEPSEEK_API_KEY，请检查 .env 配置")
        trace["error_type"] = classify_generation_error(result["error"])
        return {
            "result": result,
            "trace": trace
        }

    requirement = requirement.strip()
    if not requirement:
        result = build_default_result("需求文本不能为空")
        trace["error_type"] = classify_generation_error(result["error"])
        return {
            "result": result,
            "trace": trace
        }

    prompt = build_prompt(requirement, context)
    trace["prompt_chars"] = len(prompt)

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
        normalized = normalize_result(parsed)

        if not normalized["user_stories"] and not normalized["tasks"]:
            normalized["error"] = normalized["error"] or "模型未生成有效的用户故事与任务结果"

        trace["story_count"] = len(normalized["user_stories"])
        trace["task_count"] = len(normalized["tasks"])
        trace["error_type"] = classify_generation_error(normalized.get("error", ""))
        trace["result_status"] = "error" if normalized.get("error") else "success"

        return {
            "result": normalized,
            "trace": trace
        }

    except json.JSONDecodeError:
        result = build_default_result("模型返回内容不是合法 JSON")
        trace["error_type"] = classify_generation_error(result["error"])
        return {
            "result": result,
            "trace": trace
        }
    except Exception as e:
        result = build_default_result(f"推理失败: {str(e)}")
        trace["error_type"] = classify_generation_error(result["error"])
        return {
            "result": result,
            "trace": trace
        }


def generate_structured_data(requirement: str, context: str) -> Dict[str, Any]:
    """
    调用 DeepSeek 模型生成结构化需求、用户故事和任务拆解结果。
    """
    return generate_structured_data_with_trace(requirement, context)["result"]