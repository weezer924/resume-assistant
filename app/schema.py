from typing import TypedDict

from pydantic import BaseModel

# Schema 定义字段和类型；BaseModel 负责运行时结构校验，TypedDict 只提供类型提示。
# 它们本身不证明内容真实，也不负责写入数据库。


class SourceSpan(TypedDict):
    section: str
    level: int
    body: str
    sequence: int


# 抽取路径中，程序校验模型的原文引用后，补上选定片段的 source_sequence。
# 草稿只返回给用户，不会自动保存为 Fact；用户通过确认接口提交后才保存。
class FactDraft(BaseModel):
    claim: str
    evidence_quote: str
    source_sequence: int


# 用户提交待确认的草稿及其文档 ID；服务会重新校验来源和引用，再保存 Fact。
class ConfirmFactRequest(BaseModel):
    document_id: str
    fact_draft: FactDraft


class Document(BaseModel):
    document_id: str
    filename: str
    content: str


# 模型只提供声明和原文引用，来源段落编号由程序确定。
# Pydantic 校验结构；服务检查引用是否逐字存在于选定原文片段中。
# 引用存在不等于声明一定被引用支持，不能把这项检查当作事实真实性验证。
class ModelFactOutput(BaseModel):
    claim: str
    evidence_quote: str


# 统一提供模型标识、prompt 标识和 prompt 版本，供模型调用与 Run 记录使用。
class ExtractionConfig(BaseModel):
    model: str
    prompt_id: str
    prompt_version: str


# 记录一次抽取使用的来源、模型和 prompt 配置、时间、结果及错误。
# completed 表示抽取和引用校验成功，不表示用户已确认或已保存正式 Fact。
# failed 表示模型调用或引用校验失败；保存失败记录后，服务仍向外抛出原异常。
class ModelFactRun(BaseModel):
    document_id: str
    source_sequence: int
    model: str
    prompt_id: str
    prompt_version: str
    start_at: float
    completed_at: float
    status: str
    output: str | None
    error: str | None
