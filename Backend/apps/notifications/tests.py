import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.notifications.models import Notification
from apps.users.models import User


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def notification_user(db):
    return User.objects.create_user(
        auth0_id="notifications_contract_auth0",
        email="notifications-contract@example.com",
        username="notifications_contract_user",
        full_name="Notifications Contract User",
        date_of_birth="1997-01-01",
    )


@pytest.mark.django_db
def test_notification_list_exposes_display_fields(api_client, notification_user):
    api_client.force_authenticate(user=notification_user)
    Notification.objects.create(
        user=notification_user,
        notification_type="roadmap_ready",
        title="Roadmap ready",
        message="Your roadmap is available.",
        action_url="https://example.com/roadmap",
    )

    response = api_client.get(reverse("notifications:notification-list"))

    assert response.status_code == status.HTTP_200_OK
    first_notification = response.data["results"][0]
    assert first_notification["time_ago"]
    assert first_notification["display_type"] == "Roadmap Ready"
    assert first_notification["is_actionable"] is True


@pytest.mark.django_db
def test_notification_stats_exposes_nav_summary(api_client, notification_user):
    api_client.force_authenticate(user=notification_user)
    Notification.objects.create(
        user=notification_user,
        notification_type="job_match",
        title="New job match",
        message="A relevant job is available.",
    )

    response = api_client.get(reverse("notifications:stats"))

    assert response.status_code == status.HTTP_200_OK
    assert response.data["nav_summary"]["unread_count"] == 1
    assert response.data["nav_summary"]["recent_notifications"]


@pytest.fixture
def another_notification_user(db):
    return User.objects.create_user(
        auth0_id="notifications_other_auth0",
        email="notifications-other@example.com",
        username="notifications_other_user",
        full_name="Other Notifications User",
        date_of_birth="1997-01-01",
    )


@pytest.mark.django_db
def test_non_admin_cannot_create_notification_for_other_user(
    api_client,
    notification_user,
    another_notification_user,
):
    api_client.force_authenticate(user=notification_user)

    response = api_client.post(
        reverse("notifications:notification-list"),
        {
            "user_id": str(another_notification_user.id),
            "notification_type": "system",
            "title": "Injected",
            "message": "Should not be created",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert Notification.objects.filter(user=another_notification_user).count() == 0


@pytest.mark.django_db
def test_user_cannot_mark_another_users_notification_read(
    api_client,
    notification_user,
    another_notification_user,
):
    notification = Notification.objects.create(
        user=another_notification_user,
        notification_type="job_match",
        title="Private",
        message="Belongs to another user",
    )
    api_client.force_authenticate(user=notification_user)

    response = api_client.post(
        reverse("notifications:notification-mark-read"),
        {"notification_ids": [str(notification.id)]},
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data["count"] == 0

    notification.refresh_from_db()
    assert notification.is_read is False


@pytest.mark.django_db
def test_user_can_mark_own_notification_read(api_client, notification_user):
    notification = Notification.objects.create(
        user=notification_user,
        notification_type="job_match",
        title="Mine",
        message="Belongs to me",
    )
    api_client.force_authenticate(user=notification_user)

    response = api_client.post(
        reverse("notifications:notification-mark-read"),
        {"notification_ids": [str(notification.id)]},
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data["count"] == 1

    notification.refresh_from_db()
    assert notification.is_read is True
