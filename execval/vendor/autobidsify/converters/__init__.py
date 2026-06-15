"""
BIDS Converters — trimmed for the ExecVal desktop app.

This is a slimmed copy of autobidsify's converters/__init__.py. The original
also imports build_bids_plan from planner, which pulls in llm.py and its
LLM client dependencies (openai, ollama, dashscope). The ExecVal app only
needs execute + validate and must stay small, so those imports are omitted
here on purpose.

IMPORTANT: this file is maintained by the desktop app and is NOT overwritten
by the cross-repo sync from the autobidsify repository.
"""

from autobidsify.converters.executor import execute_bids_plan
from autobidsify.converters.validators import validate_bids_compatible

__all__ = [
    "execute_bids_plan",
    "validate_bids_compatible",
]