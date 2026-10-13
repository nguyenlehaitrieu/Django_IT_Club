
import uuid

from django import forms
from django.contrib import admin
from django.db import transaction
from .models import Announcement

from .models import (
    ProfileTheme,
    XPTransaction,
    Achievement,
    MemberAchievement,
    MemberProfile,
    MemberPost,
    ForumTopic, 
    ForumTopicImage,
)


class MemberProfileAdminForm(forms.ModelForm):
    xp_to_add = forms.IntegerField(
        label="XP muốn cộng",
        min_value=0,
        required=False,
        initial=0,
        help_text="Nhập số XP muốn cộng thêm cho thành viên.",
    )

    xp_reason = forms.CharField(
        label="Lý do cộng XP",
        max_length=200,
        required=False,
        help_text="Ví dụ: Cấp XP để kiểm thử Developer Space.",
    )

    class Meta:
        model = MemberProfile
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()
        amount = cleaned_data.get("xp_to_add") or 0
        reason = (cleaned_data.get("xp_reason") or "").strip()

        if amount > 0 and not reason:
            self.add_error(
                "xp_reason",
                "Vui lòng nhập lý do cộng XP.",
            )

        return cleaned_data


@admin.register(ProfileTheme)
class ProfileThemeAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "slug",
        "xp_cost",
        "required_likes",
        "background_key",
        "is_active",
    )
    list_editable = ("xp_cost", "required_likes", "is_active")
    search_fields = ("name", "slug")
    list_filter = ("background_key", "is_active")


@admin.register(XPTransaction)
class XPTransactionAdmin(admin.ModelAdmin):
    list_display = (
        "profile",
        "amount",
        "reason",
        "event_key",
        "created_at",
    )
    search_fields = ("profile__user__username", "event_key")
    readonly_fields = (
        "profile",
        "amount",
        "reason",
        "event_key",
        "created_at",
    )


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "description")
    search_fields = ("name", "slug")


@admin.register(MemberAchievement)
class MemberAchievementAdmin(admin.ModelAdmin):
    list_display = ("profile", "achievement", "earned_at")
    search_fields = (
        "profile__user__username",
        "achievement__name",
    )
    readonly_fields = ("profile", "achievement", "earned_at")


@admin.register(MemberProfile)
class MemberProfileAdmin(admin.ModelAdmin):
    form = MemberProfileAdminForm

    list_display = (
        "user",
        "xp",
        "active_theme",
        "updated_at",
    )
    search_fields = (
        "user__username",
        "user__email",
    )
    readonly_fields = ("xp", "updated_at")
    filter_horizontal = ("unlocked_themes",)

    @transaction.atomic
    def save_model(self, request, obj, form, change):
        # Lưu hồ sơ trước để bảo đảm obj có khóa chính.
        super().save_model(request, obj, form, change)

        amount = form.cleaned_data.get("xp_to_add") or 0
        reason = (form.cleaned_data.get("xp_reason") or "").strip()

        if amount <= 0:
            return

        # Khóa bản ghi trong lúc cập nhật XP.
        profile = MemberProfile.objects.select_for_update().get(
            pk=obj.pk
        )

        profile.xp += amount
        profile.save(update_fields=["xp", "updated_at"])

        XPTransaction.objects.create(
            profile=profile,
            amount=amount,
            reason=reason,
            event_key=f"admin-{uuid.uuid4().hex}",
        )

        obj.xp = profile.xp


@admin.register(MemberPost)
class MemberPostAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "author",
        "status",
        "created_at",
    )
    list_filter = ("status", "created_at")
    search_fields = ("title", "author__username")







@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "priority",
        "author",
        "is_published",
        "published_at",
    )
    list_filter = ("priority", "is_published", "published_at")
    search_fields = ("title", "summary", "content")
    readonly_fields = ("created_at", "updated_at")

class ForumTopicImageInline(admin.TabularInline):
    model = ForumTopicImage
    extra = 0


@admin.register(ForumTopic)
class ForumTopicAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "author",
        "category",
        "status",
        "created_at",
        "published_at",
    )

    list_filter = ("status", "category", "created_at")
    search_fields = ("title", "content", "author__username")
    readonly_fields = ("created_at", "updated_at")
    inlines = [ForumTopicImageInline]
    list_per_page = 20