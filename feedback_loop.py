"""Repo-root import for ``from feedback_loop import FeedbackLoopEngine``.

The implementation lives in ``_src/tools/feedback_loop.py``. This module only
loads that file. Importing it does not read or write the corpus.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

_IMPL = Path(__file__).resolve().parent / "_src" / "tools" / "feedback_loop.py"
_spec = importlib.util.spec_from_file_location("_autodocs_feedback_loop_impl", _IMPL)
if _spec is None or _spec.loader is None:
    raise ImportError("feedback loop implementation missing: %s" % (_IMPL,))
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)

FeedbackLoop = _module.FeedbackLoop
FeedbackLoopEngine = _module.FeedbackLoopEngine
FeedbackLoopError = _module.FeedbackLoopError
