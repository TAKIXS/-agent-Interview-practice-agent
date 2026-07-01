"""面试打分 Schema — pydantic 模型。"""

from pydantic import BaseModel, Field


class InterviewScore(BaseModel):
    """单题面试得分。"""
    technical_accuracy: float = Field(0.0, ge=0.0, le=10.0, description="技术准确度")
    depth_of_understanding: float = Field(0.0, ge=0.0, le=10.0, description="理解深度")
    clarity_of_explanation: float = Field(0.0, ge=0.0, le=10.0, description="表达清晰度")
    practical_examples: float = Field(0.0, ge=0.0, le=10.0, description="实例运用")
    overall: float = Field(0.0, ge=0.0, le=10.0, description="综合得分")
    strengths: list[str] = Field(default_factory=list, description="回答亮点")
    areas_for_improvement: list[str] = Field(default_factory=list, description="改进建议")
    model_answer_reference: str = Field("", description="参考要点")


class CodeEvaluation(BaseModel):
    """代码评审结果。"""
    correctness: float = Field(0.0, ge=0.0, le=10.0, description="正确性")
    efficiency: float = Field(0.0, ge=0.0, le=10.0, description="效率")
    best_practices: float = Field(0.0, ge=0.0, le=10.0, description="最佳实践")
    overall: float = Field(0.0, ge=0.0, le=10.0, description="综合得分")
    suggestions: list[str] = Field(default_factory=list, description="修改建议")
    improved_code: str = Field("", description="参考代码")


class QuizQuestion(BaseModel):
    """一道选择题。"""
    question: str = Field(..., description="题目")
    options: list[str] = Field(..., min_length=4, max_length=4, description="4 个选项")
    correct_index: int = Field(..., ge=0, le=3, description="正确答案索引")
    explanation: str = Field(..., description="正确选项解析")
    distractors_explanation: list[str] = Field(default_factory=list, description="错误选项陷阱说明")
