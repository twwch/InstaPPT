from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Literal

class ModelConfig(BaseModel):
    model_config = ConfigDict(extra='ignore')
    base_url: str
    api_key: str
    model: str
    temperature: float = 0.7

class SDKConfig(BaseModel):
    model_config = ConfigDict(extra='ignore')
    translator_config: ModelConfig
    optimizer_config: ModelConfig
    evaluator_config: ModelConfig
    enable_cache: bool = True

class EvaluationMetrics(BaseModel):
    model_config = ConfigDict(extra='ignore')
    accuracy: int = Field(..., description="1-10 score for Accuracy")
    fluency: int = Field(..., description="1-10 score for Fluency")
    consistency: int = Field(..., description="1-10 score for Consistency")
    terminology: int = Field(..., description="1-10 score for Terminology")
    completeness: int = Field(..., description="1-10 score for Completeness")

class EvaluationResult(BaseModel):
    model_config = ConfigDict(extra='ignore')
    metrics: EvaluationMetrics
    suggestions: str
    overall_score: float
    duration_seconds: float = 0.0

class TranslationSegment(BaseModel):
    model_config = ConfigDict(extra='ignore')
    original_text: str
    translated_text_a: Optional[str] = None
    duration_a: float = 0.0
    evaluation_a: Optional[EvaluationResult] = None
    optimized_text_c: Optional[str] = None
    duration_c: float = 0.0
    evaluation_c: Optional[EvaluationResult] = None
    final_text: Optional[str] = None # The text chosen for the final PPT (usually C, but could be A if C fails)
