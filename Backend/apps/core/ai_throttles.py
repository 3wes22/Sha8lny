"""
AI-specific rate limiting.

The single-lane Celery queue (ADR-001) can only handle one AI inference at a
time.  These throttle classes prevent a single user from flooding the queue and
blocking AI for everyone else.
"""

from __future__ import annotations

from rest_framework.throttling import UserRateThrottle


class AIBurstThrottle(UserRateThrottle):
    """Short-burst limit for AI-heavy endpoints (create assessment, submit, generate roadmap).

    Allows 3 requests per minute per authenticated user.
    """

    scope = "ai_burst"
    rate = "3/min"


class AISustainedThrottle(UserRateThrottle):
    """Sustained limit across a longer window.

    Allows 20 AI requests per hour per authenticated user.
    """

    scope = "ai_sustained"
    rate = "20/hour"
