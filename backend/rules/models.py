from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional


class DocModifier(str, Enum):
    """Modifiers injected into LLM system prompts based on deterministic rules."""
    EMPHASIZE_COMMERCIAL = "EMPHASIZE_COMMERCIAL"
    INCLUDE_DO178_DO297 = "INCLUDE_DO178_DO297"
    HW_SW_SEPARATION = "HW_SW_SEPARATION"
    ATTRITABLE_LIFECYCLE = "ATTRITABLE_LIFECYCLE"
    HIGH_TECH_RISK_MODULAR = "HIGH_TECH_RISK_MODULAR"
    COTS_REFRESH_CYCLE = "COTS_REFRESH_CYCLE"
    SUSTAINMENT_TAIL_PLANNING = "SUSTAINMENT_TAIL_PLANNING"
    MISSION_CRITICAL_VERIFICATION = "MISSION_CRITICAL_VERIFICATION"
    REUSE_TYPE_ANALYSIS = "REUSE_TYPE_ANALYSIS"


@dataclass
class RulesInput:
    # Program identity
    service_branch: Optional[str] = None        # USN, USAF, USSF, ARMY
    army_pae: Optional[str] = None              # e.g. PM_PEO_C3T

    # Cost fields (in $M)
    dev_cost_estimate: Optional[float] = None
    production_unit_cost: Optional[float] = None

    # Booleans from ProgramBrief
    attritable: Optional[bool] = None
    sustainment_tail: Optional[bool] = None
    software_large_part: Optional[bool] = None
    mission_critical: Optional[bool] = None
    safety_critical: Optional[bool] = None
    software_involved: Optional[bool] = None
    similar_programs_exist: Optional[bool] = None

    # Timeline
    timeline_months: Optional[int] = None

    # Army sub-branch (populated only when service_branch == "ARMY")
    army_branch: Optional[str] = None          # FIRES | MANEUVER | AVIATION

    # Module stats (derived from Module table)
    module_count: int = 0
    modules_with_cots: int = 0
    modules_with_tech_risk: int = 0
    modules_with_obsolescence_risk: int = 0


@dataclass
class RuleViolation:
    rule_id: str
    severity: str   # ERROR | WARN | INFO
    message: str
    field: Optional[str] = None


@dataclass
class RulesResult:
    mig_id: Optional[str] = None
    modifiers: List[DocModifier] = field(default_factory=list)
    violations: List[RuleViolation] = field(default_factory=list)
    recommended_module_count_min: Optional[int] = None
    recommended_module_count_max: Optional[int] = None
    # Arbitrary boolean flags for downstream use
    flags: dict = field(default_factory=dict)
