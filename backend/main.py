import json
import time
from typing import Any, Dict, List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from llm_module import generate_structured_data, generate_structured_data_with_trace, extract_requirement_from_code
from kb_module import get_enhanced_context, get_enhanced_payload, get_knowledge_statistics
from evaluation_module import evaluate_result

# 数据库知识库相关模块。需要配合 database.py、knowledge_models.py、seed_common_knowledge.py 使用。
try:
    from database import Base, engine, SessionLocal
    from knowledge_models import KnowledgeModule
    from seed_common_knowledge import seed_common_knowledge
    DATABASE_AVAILABLE = True
except Exception:
    Base = None
    engine = None
    SessionLocal = None
    KnowledgeModule = None
    DATABASE_AVAILABLE = False

# 用户故事相关代码生成模块。需要配合 code_module.py 使用。
try:
    from code_module import generate_related_code, generate_related_code_with_trace
    CODE_GENERATION_AVAILABLE = True
except Exception:
    generate_related_code = None
    generate_related_code_with_trace = None
    CODE_GENERATION_AVAILABLE = False


app = FastAPI(
    title="智能用户故事生成系统",
    description="基于大语言模型与数据库知识库的需求解析、用户故事生成、任务拆解、代码生成与实验评估系统",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class RequirementRequest(BaseModel):
    requirement: str = Field(..., description="单条自然语言需求文本")


class BatchRequirementRequest(BaseModel):
    requirements: List[str] = Field(..., description="多条自然语言需求文本列表")


class CodeRequirementRequest(BaseModel):
    code: str = Field(..., description="代码文本（支持多语言，建议单段完整代码）")


class KnowledgeModuleRequest(BaseModel):
    module_name: str = Field(..., description="知识模块名称")
    category: str = Field("通用软件模块", description="模块分类")
    aliases: List[str] = Field(default_factory=list, description="模块别名")
    required_elements: List[str] = Field(default_factory=list, description="必选要素")
    preconditions: List[str] = Field(default_factory=list, description="前置条件")
    exception_scenarios: List[str] = Field(default_factory=list, description="异常场景")
    typical_tasks: List[str] = Field(default_factory=list, description="典型任务")
    security_constraints: str = Field("", description="安全约束")
    description: str = Field("", description="模块说明")


class CodeGenerateRequest(BaseModel):
    requirement: str = Field("", description="原始自然语言需求")
    story: str = Field(..., description="选中的用户故事")
    tasks: List[Dict[str, Any]] = Field(default_factory=list, description="该用户故事对应的任务列表")


def success_response(data: Any, message: str = "操作成功") -> Dict[str, Any]:
    return {
        "success": True,
        "message": message,
        "data": data
    }


def error_response(message: str = "操作失败", data: Any = None) -> Dict[str, Any]:
    return {
        "success": False,
        "message": message,
        "data": data
    }


def round_ms(value: float) -> float:
    return round(max(value, 0.0), 2)


def build_performance_trace(
    total_ms: float,
    llm_ms: float = 0.0,
    knowledge_ms: float = 0.0,
    evaluation_ms: float = 0.0,
    extraction_ms: float = 0.0
) -> Dict[str, float]:
    return {
        "total_ms": round_ms(total_ms),
        "model_inference_ms": round_ms(llm_ms),
        "local_processing_ms": round_ms(total_ms - llm_ms),
        "knowledge_processing_ms": round_ms(knowledge_ms),
        "evaluation_ms": round_ms(evaluation_ms),
        "requirement_extraction_ms": round_ms(extraction_ms)
    }


def dumps_list(value: List[str]) -> str:
    return json.dumps(value or [], ensure_ascii=False)


def loads_list(value: str) -> List[str]:
    try:
        data = json.loads(value or "[]")
        return data if isinstance(data, list) else []
    except Exception:
        return []


def knowledge_row_to_dict(row: Any) -> Dict[str, Any]:
    return {
        "id": row.id,
        "module_name": row.module_name,
        "category": row.category,
        "aliases": loads_list(row.aliases),
        "required_elements": loads_list(row.required_elements),
        "preconditions": loads_list(row.preconditions),
        "exception_scenarios": loads_list(row.exception_scenarios),
        "typical_tasks": loads_list(row.typical_tasks),
        "security_constraints": row.security_constraints or "",
        "description": row.description or "",
        "is_builtin": row.is_builtin
    }


@app.on_event("startup")
def startup_event():
    """
    系统启动时初始化数据库知识库。
    如果尚未添加数据库相关文件，不影响原有用户故事生成功能运行。
    """
    if DATABASE_AVAILABLE:
        Base.metadata.create_all(bind=engine)
        seed_common_knowledge()


@app.get("/health")
def health_check():
    return success_response(
        {
            "service": "智能用户故事生成系统后端",
            "status": "running",
            "database_available": DATABASE_AVAILABLE,
            "code_generation_available": CODE_GENERATION_AVAILABLE
        },
        "服务运行正常"
    )


@app.get("/knowledge_modules")
def list_knowledge_modules():
    if not DATABASE_AVAILABLE:
        return error_response("数据库知识库模块未启用，请检查 database.py、knowledge_models.py 和 seed_common_knowledge.py")

    db = SessionLocal()
    try:
        rows = db.query(KnowledgeModule).order_by(KnowledgeModule.id.asc()).all()
        modules = [knowledge_row_to_dict(row) for row in rows]
        return success_response(
            {
                "total": len(modules),
                "modules": modules
            },
            "知识库模块查询成功"
        )
    finally:
        db.close()


@app.get("/knowledge_statistics")
def knowledge_statistics():
    if not DATABASE_AVAILABLE:
        return error_response("数据库知识库模块未启用，请检查 database.py、knowledge_models.py 和 seed_common_knowledge.py")

    try:
        return success_response(get_knowledge_statistics(), "知识库统计信息查询成功")
    except Exception as e:
        return error_response(f"知识库统计异常: {str(e)}")


@app.post("/knowledge_modules")
def create_knowledge_module(req: KnowledgeModuleRequest):
    if not DATABASE_AVAILABLE:
        return error_response("数据库知识库模块未启用，请检查 database.py、knowledge_models.py 和 seed_common_knowledge.py")

    module_name = req.module_name.strip()
    if not module_name:
        return error_response("模块名称不能为空")

    db = SessionLocal()
    try:
        exists = db.query(KnowledgeModule).filter(
            KnowledgeModule.module_name == module_name
        ).first()

        if exists:
            return error_response("该知识模块已存在")

        module = KnowledgeModule(
            module_name=module_name,
            category=req.category.strip() or "通用软件模块",
            aliases=dumps_list(req.aliases),
            required_elements=dumps_list(req.required_elements),
            preconditions=dumps_list(req.preconditions),
            exception_scenarios=dumps_list(req.exception_scenarios),
            typical_tasks=dumps_list(req.typical_tasks),
            security_constraints=req.security_constraints.strip(),
            description=req.description.strip(),
            is_builtin=False
        )

        db.add(module)
        db.commit()
        db.refresh(module)

        return success_response(
            knowledge_row_to_dict(module),
            "知识库模块新增成功"
        )
    finally:
        db.close()


@app.post("/preview_context")
def preview_context(req: RequirementRequest):
    requirement = req.requirement.strip()

    if not requirement:
        return error_response("需求文本不能为空")

    try:
        knowledge_start = time.perf_counter()
        payload = get_enhanced_payload(requirement)
        knowledge_ms = (time.perf_counter() - knowledge_start) * 1000
        return success_response(
            {
                "requirement": requirement,
                "knowledge_context": payload["context"],
                "matched_modules": payload.get("matched_modules", []),
                "trace": {
                    "knowledge": {
                        **payload.get("stats", {}),
                        "knowledge_context_chars": len(payload.get("context", ""))
                    },
                    "performance": build_performance_trace(total_ms=knowledge_ms, knowledge_ms=knowledge_ms)
                }
            },
            "知识增强上下文获取成功"
        )
    except Exception as e:
        return error_response(f"知识增强处理异常: {str(e)}")


@app.post("/generate_story")
def generate_story_endpoint(req: RequirementRequest):
    requirement = req.requirement.strip()

    if not requirement:
        return error_response("需求文本不能为空")

    try:
        total_start = time.perf_counter()
        knowledge_start = time.perf_counter()
        payload = get_enhanced_payload(requirement)
        knowledge_ms = (time.perf_counter() - knowledge_start) * 1000
        generation = generate_structured_data_with_trace(requirement, payload["context"], strategy="knowledge_enhanced")
        result = generation["result"]
        total_ms = (time.perf_counter() - total_start) * 1000
        trace = {
            "knowledge": {
                **payload.get("stats", {}),
                "knowledge_context_chars": len(payload.get("context", ""))
            },
            "generation": generation["trace"],
            "performance": build_performance_trace(
                total_ms=total_ms,
                llm_ms=generation["trace"].get("llm_inference_ms", 0.0),
                knowledge_ms=knowledge_ms
            )
        }

        if result.get("error"):
            return error_response(
                message=result["error"],
                data={
                    "requirement": requirement,
                    "knowledge_context": payload["context"],
                    "result": result,
                    "trace": trace
                }
            )

        return success_response(
            {
                "requirement": requirement,
                "knowledge_context": payload["context"],
                "matched_modules": payload.get("matched_modules", []),
                "result": result,
                "trace": trace
            },
            "用户故事与任务拆解生成成功"
        )

    except Exception as e:
        return error_response(f"后端处理异常: {str(e)}")


@app.post("/generate_batch")
def generate_batch_endpoint(req: BatchRequirementRequest):
    requirements = [
        item.strip()
        for item in req.requirements
        if item and item.strip()
    ]

    if not requirements:
        return error_response("批量需求文本不能为空")

    batch_results = []

    for index, requirement in enumerate(requirements, start=1):
        try:
            context = get_enhanced_context(requirement)
            result = generate_structured_data(requirement, context)
            is_success = not bool(result.get("error"))

            batch_results.append(
                {
                    "index": index,
                    "requirement": requirement,
                    "knowledge_context": context,
                    "result": result,
                    "success": is_success,
                    "error": result.get("error", "")
                }
            )

        except Exception as e:
            batch_results.append(
                {
                    "index": index,
                    "requirement": requirement,
                    "knowledge_context": "",
                    "result": None,
                    "success": False,
                    "error": f"第{index}条需求处理异常: {str(e)}"
                }
            )

    success_count = sum(1 for item in batch_results if item["success"])
    fail_count = len(batch_results) - success_count

    return success_response(
        {
            "total": len(batch_results),
            "success_count": success_count,
            "fail_count": fail_count,
            "results": batch_results
        },
        "批量用户故事生成完成"
    )


@app.post("/generate_and_evaluate")
def generate_and_evaluate(req: RequirementRequest):
    requirement = req.requirement.strip()

    if not requirement:
        return error_response("需求文本不能为空")

    try:
        total_start = time.perf_counter()
        knowledge_start = time.perf_counter()
        payload = get_enhanced_payload(requirement)
        knowledge_ms = (time.perf_counter() - knowledge_start) * 1000
        generation = generate_structured_data_with_trace(requirement, payload["context"], strategy="knowledge_enhanced")
        result = generation["result"]

        evaluation = None
        evaluation_ms = 0.0
        if not result.get("error"):
            evaluation_start = time.perf_counter()
            evaluation = evaluate_result(result)
            evaluation_ms = (time.perf_counter() - evaluation_start) * 1000

        total_ms = (time.perf_counter() - total_start) * 1000
        trace = {
            "knowledge": {
                **payload.get("stats", {}),
                "knowledge_context_chars": len(payload.get("context", ""))
            },
            "generation": generation["trace"],
            "performance": build_performance_trace(
                total_ms=total_ms,
                llm_ms=generation["trace"].get("llm_inference_ms", 0.0),
                knowledge_ms=knowledge_ms,
                evaluation_ms=evaluation_ms
            )
        }

        if result.get("error"):
            return error_response(
                message=result["error"],
                data={
                    "requirement": requirement,
                    "knowledge_context": payload["context"],
                    "result": result,
                    "evaluation": None,
                    "trace": trace
                }
            )

        return success_response(
            {
                "requirement": requirement,
                "knowledge_context": payload["context"],
                "matched_modules": payload.get("matched_modules", []),
                "result": result,
                "evaluation": evaluation,
                "trace": trace
            },
            "生成与评估完成"
        )

    except Exception as e:
        return error_response(f"后端处理异常: {str(e)}")


@app.post("/generate_story_from_code")
def generate_story_from_code(req: CodeRequirementRequest):
    code = req.code.strip()
    if not code:
        return error_response("代码文本不能为空")

    try:
        total_start = time.perf_counter()
        extraction_start = time.perf_counter()
        extracted_req = extract_requirement_from_code(code)
        extraction_ms = (time.perf_counter() - extraction_start) * 1000
        if not extracted_req:
            return error_response("未能从代码中提取到有效需求描述")

        knowledge_start = time.perf_counter()
        payload = get_enhanced_payload(extracted_req)
        knowledge_ms = (time.perf_counter() - knowledge_start) * 1000
        generation = generate_structured_data_with_trace(extracted_req, payload["context"], strategy="code_to_story")
        result = generation["result"]

        evaluation = None
        evaluation_ms = 0.0
        if not result.get("error"):
            evaluation_start = time.perf_counter()
            evaluation = evaluate_result(result)
            evaluation_ms = (time.perf_counter() - evaluation_start) * 1000

        total_ms = (time.perf_counter() - total_start) * 1000
        trace = {
            "knowledge": {
                **payload.get("stats", {}),
                "knowledge_context_chars": len(payload.get("context", ""))
            },
            "generation": generation["trace"],
            "performance": build_performance_trace(
                total_ms=total_ms,
                llm_ms=generation["trace"].get("llm_inference_ms", 0.0),
                knowledge_ms=knowledge_ms,
                evaluation_ms=evaluation_ms,
                extraction_ms=extraction_ms
            )
        }

        if result.get("error"):
            return error_response(
                message=result["error"],
                data={
                    "extracted_requirement": extracted_req,
                    "knowledge_context": payload["context"],
                    "result": result,
                    "evaluation": None,
                    "trace": trace
                }
            )

        return success_response(
            {
                "extracted_requirement": extracted_req,
                "knowledge_context": payload["context"],
                "matched_modules": payload.get("matched_modules", []),
                "result": result,
                "evaluation": evaluation,
                "trace": trace
            },
            "代码成功解析并生成用户故事"
        )
    except Exception as e:
        return error_response(f"代码分析异常: {str(e)}")


@app.post("/generate_code")
def generate_code_endpoint(req: CodeGenerateRequest):
    if not CODE_GENERATION_AVAILABLE:
        return error_response("代码生成模块未启用，请检查 code_module.py 是否存在并能正常导入")

    story = req.story.strip()
    if not story:
        return error_response("用户故事不能为空")

    try:
        total_start = time.perf_counter()
        generation = generate_related_code_with_trace(
            requirement=req.requirement.strip(),
            story=story,
            tasks=req.tasks
        )
        code_result = generation["result"]
        total_ms = (time.perf_counter() - total_start) * 1000
        trace = {
            "generation": generation["trace"],
            "performance": build_performance_trace(
                total_ms=total_ms,
                llm_ms=generation["trace"].get("llm_inference_ms", 0.0)
            )
        }

        if code_result.get("error"):
            return error_response(
                message=code_result["error"],
                data={
                    "story": story,
                    "tasks": req.tasks,
                    "code_result": code_result,
                    "trace": trace
                }
            )

        return success_response(
            {
                "story": story,
                "tasks": req.tasks,
                "code_result": code_result,
                "trace": trace
            },
            "相关代码生成成功"
        )

    except Exception as e:
        return error_response(f"代码生成接口异常: {str(e)}")