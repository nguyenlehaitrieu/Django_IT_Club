
from django.db import transaction

from .models import (
    MemberProfile,
    ProfileTheme,
    XPTransaction,
)


@transaction.atomic
def award_xp(profile_id, amount, reason, event_key):
    """
    Cộng XP cho một sự kiện đã được hệ thống xác thực.

    Mỗi profile chỉ nhận thưởng một lần cho mỗi event_key.
    Không nhận amount trực tiếp từ request.POST.
    """
    if (
        not isinstance(amount, int)
        or isinstance(amount, bool)
        or amount <= 0
    ):
        raise ValueError("XP phải là số nguyên dương.")

    if not event_key or len(event_key) > 100:
        raise ValueError("Mã sự kiện không hợp lệ.")

    profile = MemberProfile.objects.select_for_update().get(
        pk=profile_id
    )

    _, created = XPTransaction.objects.get_or_create(
        profile=profile,
        event_key=event_key,
        defaults={
            "amount": amount,
            "reason": reason[:200],
        },
    )

    if not created:
        return False

    profile.xp += amount
    profile.save(update_fields=["xp", "updated_at"])

    return True


@transaction.atomic
def unlock_theme(profile_id, theme_id, is_admin=False):
    """Mở khóa theme nếu thành viên đáp ứng điều kiện."""
    profile = MemberProfile.objects.select_for_update().get(
        pk=profile_id
    )

    theme = ProfileTheme.objects.get(
        pk=theme_id,
        is_active=True,
    )

    if profile.unlocked_themes.filter(pk=theme.pk).exists():
        return False, "Bạn đã mở khóa theme này rồi."

    if not is_admin:
        if profile.xp < theme.xp_cost:
            return False, (
                f"Bạn cần {theme.xp_cost} XP để mở khóa theme này."
            )

        if theme.required_likes > 0:
            return False, (
                "Theme này còn yêu cầu lượt thích. "
                "Điều kiện sẽ được kích hoạt sau khi tích hợp hệ thống Like."
            )

    profile.unlocked_themes.add(theme)

    return True, f"Đã mở khóa theme {theme.name}!"


@transaction.atomic
def equip_theme(profile_id, theme_id, is_admin=False):
    """Trang bị theme đã mở khóa."""
    profile = MemberProfile.objects.select_for_update().get(
        pk=profile_id
    )

    theme = ProfileTheme.objects.get(
        pk=theme_id,
        is_active=True,
    )

    if (
        not is_admin
        and not profile.unlocked_themes.filter(pk=theme.pk).exists()
    ):
        return False, "Bạn chưa mở khóa theme này."

    profile.active_theme = theme
    profile.save(update_fields=["active_theme", "updated_at"])

    return True, f"Đã trang bị theme {theme.name}!"
