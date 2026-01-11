"""
Task definitions for General ANoT.

Modules:
- g1_allergy: Peanut allergy safety task (G1a, G1a-v2)
"""

from .g1_allergy import (
    TASK_G1_PROMPT,
    TASK_G1_PROMPT_V2,
    TASK_REGISTRY,
    get_task,
    list_tasks,
)
