import argparse
import json
import os
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
os.chdir(SCRIPT_DIR)

import experiment_runner as runner
from database import Base, engine
from seed_common_knowledge import seed_common_knowledge


def parse_args():
    parser = argparse.ArgumentParser(description="带进度输出的完整实验执行脚本")
    parser.add_argument("--samples", default=str(runner.DEFAULT_SAMPLES_PATH), help="主实验样本 JSON 路径")
    parser.add_argument("--failures", default=str(runner.DEFAULT_FAILURE_PATH), help="失败案例 JSON 路径")
    parser.add_argument("--sample-limit", type=int, default=12, help="质量对比样本上限")
    parser.add_argument("--performance-sample-count", type=int, default=2, help="性能测试使用的样本数量")
    parser.add_argument("--repeats", type=int, default=2, help="每个并发度重复次数")
    parser.add_argument("--concurrency-levels", nargs="+", type=int, default=[1, 2], help="性能测试并发数列表")
    parser.add_argument("--output-json", default=str(runner.DEFAULT_OUTPUT_JSON), help="实验报告 JSON 输出路径")
    parser.add_argument("--output-md", default=str(runner.DEFAULT_OUTPUT_MD), help="实验报告 Markdown 输出路径")
    parser.add_argument("--manual-review-csv", default=str(runner.DEFAULT_MANUAL_REVIEW_CSV), help="人工评审模板 CSV 输出路径")
    parser.add_argument("--include-raw-results", action="store_true", help="在 JSON 中保留完整模型结果")
    return parser.parse_args()


def emit(message: str):
    print(message, flush=True)


def ensure_knowledge_base_ready():
    Base.metadata.create_all(bind=engine)
    seed_common_knowledge()


def main():
    args = parse_args()
    samples = runner.load_json(Path(args.samples))[: args.sample_limit]
    failure_cases = runner.load_json(Path(args.failures))

    if not os.getenv("DEEPSEEK_API_KEY"):
        emit("警告：未检测到 DEEPSEEK_API_KEY，实验会运行但模型结果会全部回落到错误结构。")

    emit(f"开始完整实验：主样本 {len(samples)} 条，性能样本 {args.performance_sample_count} 条，并发 {args.concurrency_levels}，重复 {args.repeats} 次。")

    ensure_knowledge_base_ready()

    knowledge_statistics = runner.get_knowledge_statistics()
    emit(
        "知识库统计："
        f"模块 {knowledge_statistics['knowledge_module_total']}，"
        f"分类 {knowledge_statistics['category_total']}，"
        f"异常场景 {knowledge_statistics['total_exception_scenarios']}。"
    )

    total_quality_jobs = len(samples) * len(runner.STRATEGIES)
    quality_records = []
    completed_quality_jobs = 0

    for sample in samples:
        for strategy in runner.STRATEGIES:
            completed_quality_jobs += 1
            emit(
                f"质量对比 {completed_quality_jobs}/{total_quality_jobs}："
                f"样本 {sample['id']}，策略 {runner.STRATEGIES[strategy]}。"
            )
            record = runner.run_quality_case(
                sample,
                strategy,
                include_raw_results=args.include_raw_results
            )
            quality_records.append(record)
            emit(
                f"完成：样本 {sample['id']}，策略 {runner.STRATEGIES[strategy]}，"
                f"得分 {record['total_score']}，故事 {record['story_count']}，任务 {record['task_count']}，"
                f"总耗时 {record['total_ms']} ms。"
            )

    quality_summary = runner.summarize_quality(quality_records)
    significance_summary = runner.summarize_significance(quality_records)
    emit("质量对比阶段完成，开始性能测试。")

    performance_summary = []
    for strategy in runner.STRATEGIES:
        for concurrency in args.concurrency_levels:
            emit(
                f"性能测试：策略 {runner.STRATEGIES[strategy]}，并发 {concurrency}，重复 {args.repeats} 次。"
            )
            result = runner.summarize_performance(
                samples=samples,
                repeats=args.repeats,
                concurrency_levels=[concurrency],
                sample_count=args.performance_sample_count,
                strategies=[strategy]
            )
            performance_summary.extend(result)
            current = result[0] if result else {}
            emit(
                f"完成：策略 {runner.STRATEGIES[strategy]}，并发 {concurrency}，"
                f"平均总耗时 {current.get('avg_total_ms', 0)} ms，"
                f"平均模型耗时 {current.get('avg_model_ms', 0)} ms。"
            )

    manual_review_path = Path(args.manual_review_csv)
    runner.write_manual_review_template(samples, manual_review_path)

    report = {
        "knowledge_statistics": knowledge_statistics,
        "sample_summary": runner.summarize_samples(samples),
        "quality_summary": quality_summary,
        "quality_records": quality_records,
        "significance_summary": significance_summary,
        "performance_summary": performance_summary,
        "failure_case_catalog": failure_cases,
        "manual_review_template": str(manual_review_path)
    }

    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    runner.dump_json(output_json, report)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_md.write_text(runner.build_markdown_report(report), encoding="utf-8")

    emit("实验完成，结果已写入：")
    emit(json.dumps({
        "output_json": str(output_json),
        "output_md": str(output_md),
        "sample_total": len(samples),
        "strategies": list(runner.STRATEGIES.values())
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()