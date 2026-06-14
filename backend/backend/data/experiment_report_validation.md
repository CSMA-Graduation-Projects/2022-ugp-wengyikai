# 实验报告

## 知识库规模

- 知识模块数：38
- 分类数：17
- 别名总数：204
- 必选要素总数：186
- 前置条件总数：73
- 异常场景总数：152
- 典型任务总数：156

## 样本分布

- 主实验样本数：1
- 来源分布：{'公开业务场景改写': 1}
- 业务域分布：{'安全认证': 1}

## 质量对比

| strategy_label | sample_count | success_rate | avg_total_score | avg_story_count | avg_task_count | avg_dependency_task_ratio | avg_failure_keyword_count | avg_total_ms | avg_model_ms |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 纯 LLM | 1 | 0.0 | 0 | 0 | 0 | 0.0 | 0 | 703.8 | 0.0 |
| LLM+规则模板 | 1 | 0.0 | 0 | 0 | 0 | 0.0 | 0 | 943.72 | 0.0 |
| LLM+知识库增强 | 1 | 0.0 | 0 | 0 | 0 | 0.0 | 0 | 804.1 | 0.0 |

## 显著性说明

| baseline_label | challenger_label | avg_delta | wins | losses | ties | p_value | significant |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 纯 LLM | LLM+知识库增强 | 0 | 0 | 0 | 1 | 1.0 | False |
| LLM+规则模板 | LLM+知识库增强 | 0 | 0 | 0 | 1 | 1.0 | False |

## 性能测试

| strategy_label | concurrency | request_count | repeats | avg_total_ms | max_total_ms | avg_model_ms | avg_local_ms | avg_evaluation_ms | avg_batch_wallclock_ms | error_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 纯 LLM | 1 | 1 | 1 | 477.77 | 477.77 | 0.0 | 477.77 | 0.0 | 481.15 | 1 |
| LLM+规则模板 | 1 | 1 | 1 | 401.12 | 401.12 | 0.0 | 401.12 | 0.0 | 404.74 | 1 |
| LLM+知识库增强 | 1 | 1 | 1 | 391.66 | 391.66 | 0.0 | 391.66 | 0.0 | 395.34 | 1 |

## 失败案例目录

| id | category | interface | expected_behavior |
| --- | --- | --- | --- |
| F01 | 空输入 | /generate_and_evaluate | 直接返回“需求文本不能为空”，且不触发模型调用。 |
| F02 | 知识库未命中 | /preview_context | trace.knowledge.context_source 应为 fallback_general_engineering，miss_reason 为 no_domain_match。 |
| F03 | 歧义输入 | /generate_and_evaluate | 评估得分应低于结构化完整需求，或在 suggestions 中体现信息不足。 |
| F04 | 冲突约束 | /generate_and_evaluate | 应在人工评审记录中标记逻辑冲突识别情况，必要时作为失败案例讨论。 |
| F05 | 空代码输入 | /generate_story_from_code | 直接返回“代码文本不能为空”。 |
| F06 | 代码生成缺失故事 | /generate_code | 直接返回“用户故事不能为空”，且不调用模型。 |

## 人工评审

- 已生成评审模板：backend\data\manual_review_template_validation.csv
- 建议采用 3 名评审者独立打分，并对每个样本的三种策略结果进行盲评。
- 统计时可分别给出自动评分结果与人工评分均值。