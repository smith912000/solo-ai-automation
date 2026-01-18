"""
Shared sales + psychology training blocks for agents.
"""

from .sales_psychology import SALES_PSYCH_PRINCIPLES, build_sales_prompt
from .objection_handling import OBJECTION_PLAYBOOK, build_objection_prompt

__all__ = [
    "SALES_PSYCH_PRINCIPLES",
    "OBJECTION_PLAYBOOK",
    "build_sales_prompt",
    "build_objection_prompt",
]
