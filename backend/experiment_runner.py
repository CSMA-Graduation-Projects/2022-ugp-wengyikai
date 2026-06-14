import argparse
import csv
import json
import math
import os
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from statistics import mean
from typing import Any, Dict, List, Optional

from evaluation_module import evaluate_result
from kb_module import get_enhanced_payload, get_knowledge_statistics
from llm_module import generate_structured_data_with_trace, get_rule_template_context


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_SAMPLES_PATH = BASE_DIR / "data" / "experiment_samples.json"
DEFAULT_FAILURE_PATH = BASE_DIR / "data" / "failure_cases.json"
DEFAULT_OUTPUT_JSON = BASE_DIR / "data" / "experiment_report.json"
DEFAULT_OUTPUT_MD = BASE_DIR / "data" / "experiment_report.md"
DEFAULT_MANUAL_REVIEW_CSV = BASE_DIR / "data" / "manual_review_template.csv"

FAILURE_KEYWORDS = ["失败", "错误", "超时", "重复", "不存在", "异常", "冲突", "无权限", "不足"]
SECURITY_KEYWORDS = ["权限", "加密", "验签", "脱敏", "认证", "审计", "风控", "日志"]
REVIEWERS = ["R1", "R2", "R3"]
STRATEGIES = {
    "plain_llm": "纯 LLM",
    "rule_template": "LLM+规则模板",
    "knowledge_enhanced": "LLM+知识库增强"
}


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def dump_json(path: Path, payload: Any):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)


def safe_mean(values: List[float]) -> float:
    return round(mean(values), 2) if values else 0.0


def build_context(strategy: str, requirement: str, knowledge_payload: Dict[str, Any]) -> str:
    if strategy == "plain_llm":
        return ""
    if strategy == "rule_template":
        return get_rule_template_context()
    return knowledge_payload.get("context", "")


def extract_text_features(result: Dict[str, Any], keywords: List[str]) -> int:
    text_parts = []
    structured = result.get("structured_requirement", {})
    text_parts.extend(structured.get("actions", []))
    text_parts.extend(structured.get("conditions", []))
    text_parts.extend(structured.get("goals", []))
    text_parts.extend(result.get("user_stories", []))
    text_parts.extend(task.get("name", "") for task in result.get("tasks", []))
    combined_text = "\n".join(text_parts)
    return sum(1 for keyword in keywords if keyword in combined_text)


def dependency_task_ratio(result: Dict[str, Any]) -> float:
    tasks = result.get("tasks", [])
    if not tasks:
        return 0.0
    dependency_tasks = sum(1 for task in tasks if task.get("depends_on"))
    return round(dependency_tasks / len(tasks), 4)


def run_quality_case(sample: Dict[str, Any], strategy: str, include_raw_results: bool = False) -> Dict[str, Any]:
    knowledge_payload = get_enhanced_payload(sample["requirement"])
    context = build_context(strategy, sample["requirement"], knowledge_payload)

    total_start = time.perf_counter()
    generation = generate_structured_data_with_trace(sample["requirement"], context, strategy=strategy)
    result = generation["result"]
    evaluation = evaluate_result(result) if not result.get("error") else None
    total_ms = (time.perf_counter() - total_start) * 1000
    model_ms = generation["trace"].get("llm_inference_ms", 0.0)

    record = {
        "sample_id": sample["id"],
        "domain": sample["domain"],
        "source_type": sample["source_type"],
        "strategy": strategy,
        "strategy_label": STRATEGIES[strategy],
        "success": not bool(result.get("error")),
        "error": result.get("error", ""),
        "matched_modules_reference": knowledge_payload.get("matched_modules", []),
        "matched_count_reference": knowledge_payload.get("stats", {}).get("matched_count", 0),
        "context_source_reference": knowledge_payload.get("stats", {}).get("context_source", ""),
        "story_count": len(result.get("user_stories", [])),
        "task_count": len(result.get("tasks", [])),
        "dependency_task_ratio": dependency_task_ratio(result),
        "failure_keyword_count": extract_text_features(result, FAILURE_KEYWORDS),
        "security_keyword_count": extract_text_features(result, SECURITY_KEYWORDS),
        "total_ms": round(total_ms, 2),
        "model_ms": round(model_ms, 2),
        "local_ms": round(max(total_ms - model_ms, 0.0), 2),
        "evaluation": evaluation,
        "trace": generation["trace"]
    }

    if evaluation:
        record["total_score"] = evaluation["total_score"]
        record["dimension_scores"] = evaluation["dimension_scores"]
    else:
        record["total_score"] = 0
        record["dimension_scores"] = {
            "structured_completeness": 0,
            "story_quality": 0,
            "task_quality": 0,
            "dependency_quality": 0
        }

    if include_raw_results:
        record["result"] = result

    return record


def summarize_samples(samples: List[Dict[str, Any]]) -> Dict[str, Any]:
    source_counter = Counter(sample["source_type"] for sample in samples)
    domain_counter = Counter(sample["domain"] for sample in samples)
    return {
        "sample_total": len(samples),
        "sources": dict(source_counter),
        "domains": dict(domain_counter)
    }


def summarize_quality(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for record in records:
        grouped[record["strategy"]].append(record)

    summary = []
    for strategy, items in grouped.items():
        success_items = [item for item in items if item["success"]]
        summary.append(
            {
                "strategy": strategy,
                "strategy_label": STRATEGIES[strategy],
                "sample_count": len(items),
                "success_rate": round(len(success_items) / len(items), 4) if items else 0.0,
                "avg_total_score": safe_mean([item["total_score"] for item in items]),
                "avg_structured_score": safe_mean([item["dimension_scores"]["structured_completeness"] for item in items]),
                "avg_story_score": safe_mean([item["dimension_scores"]["story_quality"] for item in items]),
                "avg_task_score": safe_mean([item["dimension_scores"]["task_quality"] for item in items]),
                "avg_dependency_score": safe_mean([item["dimension_scores"]["dependency_quality"] for item in items]),
                "avg_story_count": safe_mean([item["story_count"] for item in items]),
                "avg_task_count": safe_mean([item["task_count"] for item in items]),
                "avg_dependency_task_ratio": safe_mean([item["dependency_task_ratio"] for item in items]),
                "avg_failure_keyword_count": safe_mean([item["failure_keyword_count"] for item in items]),
                "avg_security_keyword_count": safe_mean([item["security_keyword_count"] for item in items]),
                "avg_total_ms": safe_mean([item["total_ms"] for item in items]),
                "max_total_ms": round(max((item["total_ms"] for item in items), default=0.0), 2),
                "avg_model_ms": safe_mean([item["model_ms"] for item in items]),
                "avg_local_ms": safe_mean([item["local_ms"] for item in items])
            }
        )

    return summary


def exact_sign_test_p_value(win_count: int, loss_count: int) -> float:
    trials = win_count + loss_count
    if trials == 0:
        return 1.0

    tail = min(win_count, loss_count)
    probability = sum(math.comb(trials, index) for index in range(0, tail + 1)) / (2 ** trials)
    return round(min(1.0, probability * 2), 4)


def summarize_significance(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    score_map: Dict[str, Dict[str, int]] = defaultdict(dict)
    for record in records:
        score_map[record["sample_id"]][record["strategy"]] = record["total_score"]

    comparisons = []
    for baseline in ["plain_llm", "rule_template"]:
        wins = 0
        losses = 0
        ties = 0
        deltas = []

        for sample_scores in score_map.values():
            if baseline not in sample_scores or "knowledge_enhanced" not in sample_scores:
                continue

            delta = sample_scores["knowledge_enhanced"] - sample_scores[baseline]
            deltas.append(delta)
            if delta > 0:
                wins += 1
            elif delta < 0:
                losses += 1
            else:
                ties += 1

        p_value = exact_sign_test_p_value(wins, losses)
        comparisons.append(
            {
                "baseline": baseline,
                "baseline_label": STRATEGIES[baseline],
                "challenger": "knowledge_enhanced",
                "challenger_label": STRATEGIES["knowledge_enhanced"],
                "avg_delta": safe_mean(deltas),
                "wins": wins,
                "losses": losses,
                "ties": ties,
                "p_value": p_value,
                "significant": p_value < 0.05
            }
        )

    return comparisons


def run_performance_case(sample: Dict[str, Any], strategy: str) -> Dict[str, Any]:
    knowledge_payload = get_enhanced_payload(sample["requirement"])
    context = build_context(strategy, sample["requirement"], knowledge_payload)

    total_start = time.perf_counter()
    generation = generate_structured_data_with_trace(sample["requirement"], context, strategy=strategy)
    result = generation["result"]

    evaluation_ms = 0.0
    if not result.get("error"):
        evaluation_start = time.perf_counter()
        evaluate_result(result)
        evaluation_ms = (time.perf_counter() - evaluation_start) * 1000

    total_ms = (time.perf_counter() - total_start) * 1000
    model_ms = generation["trace"].get("llm_inference_ms", 0.0)

    return {
        "strategy": strategy,
        "sample_id": sample["id"],
        "success": not bool(result.get("error")),
        "total_ms": round(total_ms, 2),
        "model_ms": round(model_ms, 2),
        "local_ms": round(max(total_ms - model_ms, 0.0), 2),
        "evaluation_ms": round(evaluation_ms, 2)
    }


def summarize_performance(
    samples: List[Dict[str, Any]],
    repeats: int,
    concurrency_levels: List[int],
    sample_count: int,
    strategies: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    if not samples:
        return []

    selected_samples = samples[: max(sample_count, 1)]
    selected_strategies = strategies or list(STRATEGIES.keys())
    summary = []

    for strategy in selected_strategies:
        for concurrency in concurrency_levels:
            total_records = []
            wallclock_ms_list = []

            for _ in range(repeats):
                dispatch_samples = [selected_samples[index % len(selected_samples)] for index in range(concurrency)]
                batch_start = time.perf_counter()

                with ThreadPoolExecutor(max_workers=concurrency) as executor:
                    futures = [executor.submit(run_performance_case, sample, strategy) for sample in dispatch_samples]
                    for future in as_completed(futures):
                        total_records.append(future.result())

                wallclock_ms_list.append((time.perf_counter() - batch_start) * 1000)

            summary.append(
                {
                    "strategy": strategy,
                    "strategy_label": STRATEGIES[strategy],
                    "concurrency": concurrency,
                    "request_count": len(total_records),
                    "repeats": repeats,
                    "avg_total_ms": safe_mean([item["total_ms"] for item in total_records]),
                    "max_total_ms": round(max((item["total_ms"] for item in total_records), default=0.0), 2),
                    "avg_model_ms": safe_mean([item["model_ms"] for item in total_records]),
                    "avg_local_ms": safe_mean([item["local_ms"] for item in total_records]),
                    "avg_evaluation_ms": safe_mean([item["evaluation_ms"] for item in total_records]),
                    "avg_batch_wallclock_ms": safe_mean(wallclock_ms_list),
                    "error_count": sum(1 for item in total_records if not item["success"])
                }
            )

    return summary


def write_manual_review_template(samples: List[Dict[str, Any]], path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "sample_id",
                "strategy",
                "strategy_label",
                "reviewer_id",
                "completeness_1_5",
                "exception_coverage_1_5",
                "dependency_rationality_1_5",
                "code_usefulness_1_5",
                "overall_1_5",
                "comments"
            ]
        )
        writer.writeheader()
        for sample in samples:
            for strategy, label in STRATEGIES.items():
                for reviewer in REVIEWERS:
                    writer.writerow(
                        {
                            "sample_id": sample["id"],
                            "strategy": strategy,
                            "strategy_label": label,
                            "reviewer_id": reviewer,
                            "completeness_1_5": "",
                            "exception_coverage_1_5": "",
                            "dependency_rationality_1_5": "",
                            "code_usefulness_1_5": "",
                            "overall_1_5": "",
                            "comments": ""
                        }
                    )


def to_markdown_table(rows: List[Dict[str, Any]], columns: List[str]) -> str:
    if not rows:
        return "无数据\n"

    header = "| " + " | ".join(columns) + " |"
    divider = "| " + " | ".join(["---"] * len(columns)) + " |"
    body = []
    for row in rows:
        body.append("| " + " | ".join(str(row.get(column, "")) for column in columns) + " |")
    return "\n".join([header, divider, *body]) + "\n"


def build_markdown_report(report: Dict[str, Any]) -> str:
    knowledge = report["knowledge_statistics"]
    sample_summary = report["sample_summary"]

    lines = [
        "# 实验报告",
        "",
        "## 知识库规模",
        "",
        f"- 知识模块数：{knowledge['knowledge_module_total']}",
        f"- 分类数：{knowledge['category_total']}",
        f"- 别名总数：{knowledge['total_aliases']}",
        f"- 必选要素总数：{knowledge['total_required_elements']}",
        f"- 前置条件总数：{knowledge['total_preconditions']}",
        f"- 异常场景总数：{knowledge['total_exception_scenarios']}",
        f"- 典型任务总数：{knowledge['total_typical_tasks']}",
        "",
        "## 样本分布",
        "",
        f"- 主实验样本数：{sample_summary['sample_total']}",
        f"- 来源分布：{sample_summary['sources']}",
        f"- 业务域分布：{sample_summary['domains']}",
        "",
        "## 质量对比",
        "",
        to_markdown_table(
            report["quality_summary"],
            [
                "strategy_label",
                "sample_count",
                "success_rate",
                "avg_total_score",
                "avg_story_count",
                "avg_task_count",
                "avg_dependency_task_ratio",
                "avg_failure_keyword_count",
                "avg_total_ms",
                "avg_model_ms"
            ]
        ),
        "## 显著性说明",
        "",
        to_markdown_table(
            report["significance_summary"],
            [
                "baseline_label",
                "challenger_label",
                "avg_delta",
                "wins",
                "losses",
                "ties",
                "p_value",
                "significant"
            ]
        ),
        "## 性能测试",
        "",
        to_markdown_table(
            report["performance_summary"],
            [
                "strategy_label",
                "concurrency",
                "request_count",
                "repeats",
                "avg_total_ms",
                "max_total_ms",
                "avg_model_ms",
                "avg_local_ms",
                "avg_evaluation_ms",
                "avg_batch_wallclock_ms",
                "error_count"
            ]
        ),
        "## 失败案例目录",
        "",
        to_markdown_table(
            report["failure_case_catalog"],
            ["id", "category", "interface", "expected_behavior"]
        ),
        "## 人工评审",
        "",
        f"- 已生成评审模板：{report['manual_review_template']}",
        "- 建议采用 3 名评审者独立打分，并对每个样本的三种策略结果进行盲评。",
        "- 统计时可分别给出自动评分结果与人工评分均值。"
    ]
    return "\n".join(lines)


def parse_args():
    parser = argparse.ArgumentParser(description="运行论文实验对比和性能测试")
    parser.add_argument("--samples", default=str(DEFAULT_SAMPLES_PATH), help="主实验样本 JSON 路径")
    parser.add_argument("--failures", default=str(DEFAULT_FAILURE_PATH), help="失败案例 JSON 路径")
    parser.add_argument("--sample-limit", type=int, default=12, help="质量对比样本上限")
    parser.add_argument("--performance-sample-count", type=int, default=2, help="性能测试使用的样本数量")
    parser.add_argument("--repeats", type=int, default=3, help="每个并发度重复次数")
    parser.add_argument("--concurrency-levels", nargs="+", type=int, default=[1, 2], help="性能测试并发数列表")
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON), help="实验报告 JSON 输出路径")
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD), help="实验报告 Markdown 输出路径")
    parser.add_argument("--manual-review-csv", default=str(DEFAULT_MANUAL_REVIEW_CSV), help="人工评审模板 CSV 输出路径")
    parser.add_argument("--include-raw-results", action="store_true", help="在 JSON 中保留完整模型结果")
    return parser.parse_args()


def main():
    args = parse_args()
    samples = load_json(Path(args.samples))[: args.sample_limit]
    failure_cases = load_json(Path(args.failures))

    if not os.getenv("DEEPSEEK_API_KEY"):
        print("警告：未检测到 DEEPSEEK_API_KEY，实验会运行但模型结果会全部回落到错误结构。")

    knowledge_statistics = get_knowledge_statistics()
    quality_records = [
        run_quality_case(sample, strategy, include_raw_results=args.include_raw_results)
        for sample in samples
        for strategy in STRATEGIES
    ]
    quality_summary = summarize_quality(quality_records)
    significance_summary = summarize_significance(quality_records)
    performance_summary = summarize_performance(
        samples=samples,
        repeats=args.repeats,
        concurrency_levels=args.concurrency_levels,
        sample_count=args.performance_sample_count
    )

    manual_review_path = Path(args.manual_review_csv)
    write_manual_review_template(samples, manual_review_path)

    report = {
        "knowledge_statistics": knowledge_statistics,
        "sample_summary": summarize_samples(samples),
        "quality_summary": quality_summary,
        "quality_records": quality_records,
        "significance_summary": significance_summary,
        "performance_summary": performance_summary,
        "failure_case_catalog": failure_cases,
        "manual_review_template": str(manual_review_path)
    }

    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    dump_json(output_json, report)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_md.write_text(build_markdown_report(report), encoding="utf-8")

    print(json.dumps({
        "output_json": str(output_json),
        "output_md": str(output_md),
        "knowledge_module_total": knowledge_statistics["knowledge_module_total"],
        "sample_total": len(samples),
        "strategies": list(STRATEGIES.values())
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
