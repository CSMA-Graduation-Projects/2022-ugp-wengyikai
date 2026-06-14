from typing import Dict, Any, List


def evaluate_result(result: Dict[str, Any]) -> Dict[str, Any]:
    structured = result.get("structured_requirement", {})
    stories = result.get("user_stories", [])
    tasks = result.get("tasks", [])

    roles = structured.get("roles", [])
    actions = structured.get("actions", [])
    conditions = structured.get("conditions", [])
    goals = structured.get("goals", [])

    structured_score = 0
    structured_score += 10 if roles else 0
    structured_score += 10 if actions else 0
    structured_score += 5 if conditions else 0
    structured_score += 10 if goals else 0

    story_score = 0
    if stories:
        valid_story_count = 0
        for s in stories:
            if "作为" in s and "我想要" in s and "以便" in s:
                valid_story_count += 1
        story_score = min(25, 10 + valid_story_count * 5)

    task_score = 0
    if tasks:
        task_score += 15 if len(tasks) >= 2 else 5

        valid_type_count = 0
        for t in tasks:
            if t.get("type") in ["frontend", "backend", "database"]:
                valid_type_count += 1
        if valid_type_count == len(tasks):
            task_score += 5

    dependency_score = 0
    if tasks:
        dep_field_ok = 0
        for t in tasks:
            if "depends_on" in t and isinstance(t["depends_on"], list):
                dep_field_ok += 1
        if dep_field_ok == len(tasks):
            dependency_score = 20
        else:
            dependency_score = 8

    total_score = structured_score + story_score + task_score + dependency_score
    total_score = min(total_score, 100)

    suggestions: List[str] = []
    if not roles:
        suggestions.append("建议补充需求中的角色信息。")
    if not actions:
        suggestions.append("建议补充关键业务行为。")
    if not goals:
        suggestions.append("建议补充业务目标或价值描述。")
    if not stories:
        suggestions.append("当前未生成有效用户故事，建议优化需求表达。")
    if len(tasks) < 2:
        suggestions.append("任务拆解粒度偏粗，建议进一步细化。")
    if not any(t.get("depends_on") for t in tasks if isinstance(t.get("depends_on"), list)):
        suggestions.append("依赖关系较弱，建议补充任务前后顺序。")

    if not suggestions:
        suggestions.append("当前生成结果整体较完整，可继续优化知识库覆盖范围。")

    return {
        "total_score": total_score,
        "dimension_scores": {
            "structured_completeness": structured_score,
            "story_quality": story_score,
            "task_quality": task_score,
            "dependency_quality": dependency_score
        },
        "summary": get_summary(total_score),
        "suggestions": suggestions
    }


def get_summary(score: int) -> str:
    if score >= 85:
        return "结果较好，结构完整性和任务拆解质量较高。"
    if score >= 70:
        return "结果基本可用，但仍有一定优化空间。"
    if score >= 60:
        return "结果一般，建议进一步优化提示词和知识增强。"
    return "结果较弱，建议重新组织需求描述并完善知识库。"