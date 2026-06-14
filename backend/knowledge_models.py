# knowledge_models.py
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from database import Base


class KnowledgeModule(Base):
    """
    通用软件业务知识库表。
    每一条记录对应一个常见业务模块，例如登录、订单、支付、审批流等。
    """
    __tablename__ = "knowledge_module"

    id = Column(Integer, primary_key=True, index=True)
    module_name = Column(String(100), unique=True, index=True, nullable=False)
    category = Column(String(100), default="通用软件模块")

    # 以下字段用 JSON 字符串保存，便于兼容 SQLite
    aliases = Column(Text, default="[]")
    required_elements = Column(Text, default="[]")
    preconditions = Column(Text, default="[]")
    exception_scenarios = Column(Text, default="[]")
    typical_tasks = Column(Text, default="[]")

    security_constraints = Column(Text, default="")
    description = Column(Text, default="")

    is_builtin = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)