
from .models import MemberProfile, ProfileTheme, ForumTopic



def active_theme(request):
    default_key = "cyber_blue"

    if not request.user.is_authenticated:
        return {"active_theme_key": default_key}

    profile = (
        MemberProfile.objects
        .filter(user=request.user)
        .select_related("active_theme")
        .first()
    )

    if profile and profile.active_theme:
        return {
            "active_theme_key": profile.active_theme.background_key
        }

    return {"active_theme_key": default_key}



def forum_moderation_access(request):
    user = request.user

    can_moderate = (
        user.is_authenticated
        and (
            user.is_superuser
            or user.groups.filter(name__in=["Admin", "Editor"]).exists()
        )
    )

    pending_count = 0

    if can_moderate:
        pending_count = ForumTopic.objects.filter(status="pending").count()

    return {
        "can_moderate_forum_nav": can_moderate,
        "forum_pending_count": pending_count,
    }

    user = request.user

    can_moderate = (
        user.is_authenticated
        and (
            user.is_superuser
            or user.groups.filter(name__in=["Admin", "Editor"]).exists()
        )
    )

    return {
        "can_moderate_forum_nav": can_moderate,
    }



