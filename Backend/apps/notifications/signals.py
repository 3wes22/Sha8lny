"""
Notification Signals

Defines custom signals for notification and event-driven features.
These signals enable decoupled components to react to events across the platform.
"""

from django.dispatch import Signal

# Notification events
notification_created = Signal()  # Fired when a notification is created
notification_read = Signal()  # Fired when a notification is marked as read
notification_deleted = Signal()  # Fired when a notification is deleted

# Progress events
milestone_achieved = Signal()  # Fired when a user achieves a milestone
course_completed = Signal()  # Fired when a user completes a course
phase_completed = Signal()  # Fired when a user completes a roadmap phase
roadmap_completed = Signal()  # Fired when a user completes entire roadmap

# Learning events
learning_session_started = Signal()  # Fired when user starts learning
learning_session_ended = Signal()  # Fired when user ends learning session
streak_updated = Signal()  # Fired when user's streak is updated

# Roadmap events
roadmap_generated = Signal()  # Fired when AI generates a roadmap
roadmap_updated = Signal()  # Fired when roadmap is updated

# Assessment events
assessment_submitted = Signal()  # Fired when assessment is submitted
assessment_completed = Signal()  # Fired when assessment results are generated

# Job events
job_match_found = Signal()  # Fired when a job match is identified
job_application_submitted = Signal()  # Fired when user applies to a job

# Career tools events
resume_generated = Signal()  # Fired when resume is generated
resume_optimized = Signal()  # Fired when ATS optimization completes
portfolio_published = Signal()  # Fired when portfolio is made public

# Advisory events
chat_message_sent = Signal()  # Fired when user sends chat message
chat_response_generated = Signal()  # Fired when AI generates response
