"""Pydantic schemas for graph state and structured outputs."""

from __future__ import annotations

from typing import Annotated, Any, Literal

from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field


class SourceItem(BaseModel):
    title: str = "Untitled"
    url: str = ""
    summary: str = ""
    source_type: Literal[
        "official_docs",
        "github",
        "release_notes",
        "vendor_docs",
        "technical_blog",
        "other",
    ] = "other"
    reliability: Literal["high", "medium", "low"] = "medium"


class RawFrameworkFact(BaseModel):
    framework: str = "unknown from source"
    fact: str
    source_url: str
    reliability: Literal["high", "medium", "low"] = "medium"


class FrameworkProfile(BaseModel):
    name: str
    main_purpose: str = "unknown from sources"
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    orchestration_style: str = "unknown from sources"
    rag_support: str = "unknown from sources"
    tool_support: str = "unknown from sources"
    workflow_control: str = "unknown from sources"
    state_management: str = "unknown from sources"
    human_in_the_loop: str = "unknown from sources"
    observability: str = "unknown from sources"
    production_readiness: str = "unknown from sources"
    enterprise_suitability: str = "unknown from sources"
    source_urls: list[str] = Field(default_factory=list)


class ComparisonItem(BaseModel):
    framework: str
    score: int = Field(ge=0, le=25)
    max_score: int = 25
    why_it_fits: str
    main_tradeoff: str
    best_for_this_client_if: str


class FrameworkComparison(BaseModel):
    comparison: list[ComparisonItem] = Field(default_factory=list)
    winner: str | None = None
    runner_up: str | None = None
    decision_reason: str = ""
    confidence: Literal["high", "medium", "low"] = "medium"


class AgentBridgeState(BaseModel):
    messages: Annotated[list, add_messages] = Field(default_factory=list)
    user_question: str | None = None
    platform_description: str | None = None
    uploaded_document_ids: list[str] = Field(default_factory=list)
    input_check_passed: bool = False
    missing_items: list[str] = Field(default_factory=list)
    clarification_questions: list[str] = Field(default_factory=list)
    client_context: dict[str, Any] | None = None
    research_queries: list[str] = Field(default_factory=list)
    research_sources: list[dict[str, Any]] = Field(default_factory=list)
    raw_framework_facts: list[dict[str, Any]] = Field(default_factory=list)
    framework_profiles: list[dict[str, Any]] = Field(default_factory=list)
    framework_comparison: dict[str, Any] | None = None
    final_recommendation: str | None = None
    final_answer: str | None = None


class InputCheckResult(BaseModel):
    can_continue: bool = Field(description="True when the workflow can continue to context extraction.")
    user_question: str | None = Field(default=None, description="Cleaned framework-selection question or goal.")
    platform_description: str | None = Field(default=None, description="Client/platform context found in the conversation.")
    missing_items: list[str] = Field(default_factory=list)
    clarification_questions: list[str] = Field(default_factory=list)


class ClientContextResult(BaseModel):
    company_context: str | None = None
    industry: str | None = None
    company_size: str | None = None
    tech_stack: list[str] = Field(default_factory=list)
    hosting_or_deployment: list[str] = Field(default_factory=list)
    data_sources: list[str] = Field(default_factory=list)
    integrations: list[str] = Field(default_factory=list)
    security_constraints: list[str] = Field(default_factory=list)
    compliance_constraints: list[str] = Field(default_factory=list)
    team_constraints: list[str] = Field(default_factory=list)
    workflow_requirements: list[str] = Field(default_factory=list)
    latency_or_budget: list[str] = Field(default_factory=list)
    framework_selection_needs: list[str] = Field(default_factory=list)


class FrameworkResearchResult(BaseModel):
    research_queries: list[str] = Field(default_factory=list)
    sources: list[SourceItem] = Field(default_factory=list)
    raw_framework_facts: list[RawFrameworkFact] = Field(default_factory=list)


class FrameworkProfilesResult(BaseModel):
    framework_profiles: list[FrameworkProfile] = Field(default_factory=list)
