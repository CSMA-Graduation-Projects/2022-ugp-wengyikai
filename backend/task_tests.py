import json
import os
import time
from pathlib import Path
from statistics import mean
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient

import evaluation_module
import kb_module
import llm_module
from main import app


BASE_DIR = Path(__file__).resolve().parent
FAILURE_CASES_PATH = BASE_DIR / "data" / "failure_cases.json"
client = TestClient(app)


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def fake_llm_response(content: str):
    return SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content=content)
            )
        ]
    )


def assert_true(condition: bool, name: str, detail: str):
    if not condition:
        raise AssertionError(f"{name} 失败: {detail}")
    return {
        "name": name,
        "status": "passed",
        "detail": detail
    }


def run_unit_checks():
    checks = []

    normalized = kb_module.normalize_text(" 注册登录类 ")
    checks.append(assert_true(normalized == "注册登录", "normalize_text", normalized))

    payload = kb_module.get_enhanced_payload("用户可以注册并登录系统，还要支持验证码校验")
    checks.append(
        assert_true(
            payload["stats"]["matched_count"] >= 2,
            "knowledge_hit",
            f"命中模块: {payload['matched_modules']}"
        )
    )

    fallback_payload = kb_module.get_enhanced_payload("量子密钥分发卫星链路遥测控制台")
    checks.append(
        assert_true(
            fallback_payload["stats"]["context_source"] == "fallback_general_engineering",
            "knowledge_fallback",
            fallback_payload["stats"]["context_source"]
        )
    )

    mock_input = {
        "structured_requirement": {
            "roles": ["用户"],
            "actions": ["登录"],
            "conditions": ["账号存在"],
            "goals": ["访问系统"]
        },
        "user_stories": ["作为用户，我想要登录系统，以便访问功能"],
        "tasks": [
            {
                "id": "T1",
                "name": "设计登录页面",
                "type": "frontend",
                "story": "作为用户，我想要登录系统，以便访问功能",
                "depends_on": []
            },
            {
                "id": "T2",
                "name": "实现登录接口",
                "type": "backend",
                "story": "作为用户，我想要登录系统，以便访问功能",
                "depends_on": ["T1"]
            }
        ]
    }
    evaluation = evaluation_module.evaluate_result(mock_input)
    checks.append(
        assert_true(
            evaluation["total_score"] >= 80,
            "evaluation_score",
            f"得分: {evaluation['total_score']}"
        )
    )

    with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "mock-key"}, clear=False):
        with patch.object(
            llm_module.client.chat.completions,
            "create",
            return_value=fake_llm_response("not-json")
        ):
            generation = llm_module.generate_structured_data_with_trace("用户登录", "规则模板", strategy="mock")
            checks.append(
                assert_true(
                    generation["trace"]["error_type"] == "invalid_json",
                    "invalid_json_classification",
                    generation["trace"]["error_type"]
                )
            )

    with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "mock-key"}, clear=False):
        with patch.object(
            llm_module.client.chat.completions,
            "create",
            side_effect=RuntimeError("gateway timeout")
        ):
            generation = llm_module.generate_structured_data_with_trace("用户登录", "规则模板", strategy="mock")
            checks.append(
                assert_true(
                    generation["trace"]["error_type"] == "inference_error",
                    "inference_error_classification",
                    generation["result"]["error"]
                )
            )

    return checks


def run_endpoint_checks():
    checks = []

    health = client.get("/health")
    checks.append(assert_true(health.status_code == 200, "health_endpoint", str(health.status_code)))

    knowledge_stats = client.get("/knowledge_statistics")
    knowledge_data = knowledge_stats.json()["data"]
    checks.append(
        assert_true(
            knowledge_data["knowledge_module_total"] >= 30,
            "knowledge_statistics_endpoint",
            f"模块数: {knowledge_data['knowledge_module_total']}"
        )
    )

    preview = client.post("/preview_context", json={"requirement": "用户登录并支付订单"})
    preview_data = preview.json()["data"]
    checks.append(
        assert_true(
            preview_data["trace"]["knowledge"]["matched_count"] >= 2,
            "preview_context_trace",
            f"命中模块: {preview_data['matched_modules']}"
        )
    )

    failure_cases = load_json(FAILURE_CASES_PATH)

    empty_requirement = next(case for case in failure_cases if case["id"] == "F01")
    response = client.post("/generate_and_evaluate", json={"requirement": empty_requirement["payload"]})
    response_json = response.json()
    checks.append(
        assert_true(
            response_json["success"] is False and "不能为空" in response_json["message"],
            "empty_requirement_guard",
            response_json["message"]
        )
    )

    kb_miss = next(case for case in failure_cases if case["id"] == "F02")
    response = client.post("/preview_context", json={"requirement": kb_miss["payload"]})
    response_json = response.json()
    checks.append(
        assert_true(
            response_json["data"]["trace"]["knowledge"]["miss_reason"] == "no_domain_match",
            "knowledge_miss_case",
            response_json["data"]["trace"]["knowledge"]["miss_reason"]
        )
    )

    empty_code = next(case for case in failure_cases if case["id"] == "F05")
    response = client.post("/generate_story_from_code", json={"code": empty_code["payload"]})
    response_json = response.json()
    checks.append(
        assert_true(
            response_json["success"] is False and "代码文本不能为空" in response_json["message"],
            "empty_code_guard",
            response_json["message"]
        )
    )

    empty_story = next(case for case in failure_cases if case["id"] == "F06")
    response = client.post(
        "/generate_code",
        json={
            "requirement": "用户登录",
            "story": empty_story["payload"],
            "tasks": []
        }
    )
    response_json = response.json()
    checks.append(
        assert_true(
            response_json["success"] is False and "用户故事不能为空" in response_json["message"],
            "empty_story_guard",
            response_json["message"]
        )
    )

    return checks


def run_local_performance_checks(iterations: int = 10):
    jobs = [
        ("GET", "/health", None),
        ("GET", "/knowledge_statistics", None),
        ("POST", "/preview_context", {"requirement": "用户登录并支付订单"})
    ]
    report = []

    for method, path, payload in jobs:
        latencies = []
        for _ in range(iterations):
            start = time.perf_counter()
            if method == "GET":
                client.get(path)
            else:
                client.post(path, json=payload)
            latencies.append((time.perf_counter() - start) * 1000)

        report.append(
            {
                "path": path,
                "iterations": iterations,
                "avg_ms": round(mean(latencies), 2),
                "max_ms": round(max(latencies), 2)
            }
        )

    return report


def run_optional_real_llm_smoke():
    if os.getenv("RUN_REAL_LLM_SMOKE") != "1":
        return {
            "enabled": False,
            "status": "skipped"
        }

    response = client.post("/generate_and_evaluate", json={"requirement": "用户登录并支付订单"})
    payload = response.json()
    data = payload.get("data") or {}

    return {
        "enabled": True,
        "status": "passed" if payload.get("success") else "failed",
        "matched_modules": data.get("matched_modules", []),
        "total_score": ((data.get("evaluation") or {}).get("total_score")) or 0,
        "performance": (data.get("trace") or {}).get("performance", {})
    }


def main():
    unit_checks = run_unit_checks()
    endpoint_checks = run_endpoint_checks()
    performance_checks = run_local_performance_checks()
    llm_smoke = run_optional_real_llm_smoke()

    report = {
        "unit_checks": unit_checks,
        "endpoint_checks": endpoint_checks,
        "local_performance": performance_checks,
        "real_llm_smoke": llm_smoke
    }

    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

