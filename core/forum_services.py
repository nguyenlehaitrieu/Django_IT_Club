
from django.db import transaction
from django.core.exceptions import ValidationError

from .models import (
    MemberProfile,
    ForumTopic,
    ForumComment,
    ForumLike,
)
from .services import award_xp


XP_LIKE_TOPIC = 1
XP_RECEIVED_LIKE = 10
XP_COMMENT_TOPIC = 2


def get_member_profile(user):
    """Lấy hoặc tạo hồ sơ thành viên."""
    if not user or not user.is_authenticated:
        raise ValidationError("Bạn cần đăng nhập.")

    profile, _ = MemberProfile.objects.get_or_create(user=user)
    return profile


@transaction.atomic
def like_topic(user, topic_id):
    """Like topic công khai, không cho tự Like hoặc Like trùng."""
    profile = get_member_profile(user)

    topic = ForumTopic.objects.select_for_update().filter(
        pk=topic_id,
        status="published",
    ).first()

    if topic is None:
        raise ValidationError(
            "Chủ đề không tồn tại hoặc chưa được công khai."
        )

    if topic.author_id == user.pk:
        raise ValidationError("Bạn không thể tự thích bài viết của mình.")

    _, created = ForumLike.objects.get_or_create(
        topic=topic,
        user=user,
    )

    if not created:
        return False, "Bạn đã thích chủ đề này rồi."

    award_xp(
        profile_id=profile.pk,
        amount=XP_LIKE_TOPIC,
        reason="Thích một chủ đề diễn đàn",
        event_key=f"forum_like_given:{topic.pk}",
    )

    author_profile = MemberProfile.objects.filter(
        user_id=topic.author_id,
    ).first()

    if author_profile:
        award_xp(
            profile_id=author_profile.pk,
            amount=XP_RECEIVED_LIKE,
            reason="Chủ đề nhận được lượt thích",
            event_key=f"forum_like_received:{topic.pk}:{user.pk}",
        )

    return True, "Đã thích chủ đề thành công!"


@transaction.atomic
def create_comment(user, topic_id, content, parent_id=None):
    """Tạo bình luận hoặc trả lời bình luận trong topic công khai."""
    profile = get_member_profile(user)
    content = (content or "").strip()

    if not content:
        raise ValidationError("Nội dung bình luận không được để trống.")

    if len(content) > 5000:
        raise ValidationError("Bình luận không được vượt quá 5000 ký tự.")

    topic = ForumTopic.objects.select_for_update().filter(
        pk=topic_id,
        status="published",
    ).first()

    if topic is None:
        raise ValidationError(
            "Chủ đề không tồn tại hoặc chưa được công khai."
        )

    parent = None

    if parent_id not in (None, ""):
        parent = ForumComment.objects.filter(
        pk=parent_id,
        topic_id=topic.pk,
        status="published",
        is_deleted=False,
    ).first()

        if parent is None:
            raise ValidationError(
                "Bình luận được trả lời không tồn tại "
                "hoặc không còn công khai."
            )

    comment = ForumComment.objects.create(
        topic=topic,
        author=user,
        content=content,
        parent=parent,
        status="published",
    )

    if topic.author_id != user.pk:
        award_xp(
            profile_id=profile.pk,
            amount=XP_COMMENT_TOPIC,
            reason="Bình luận trong chủ đề của thành viên khác",
            event_key=f"forum_comment:{topic.pk}",
        )

    return comment


@transaction.atomic
def delete_own_comment(user, comment_id, topic_id=None):
    """
    Xóa mềm bình luận của chính mình.
    Giữ lại bản ghi để không mất ngữ cảnh phản hồi.
    """
    if not user or not user.is_authenticated:
        raise ValidationError("Bạn cần đăng nhập.")

    filters = {
        "pk": comment_id,
        "author": user,
    }

    if topic_id is not None:
        filters["topic_id"] = topic_id

    comment = (
        ForumComment.objects
        .select_for_update()
        .filter(**filters)
        .first()
    )

    if comment is None:
        raise ValidationError(
            "Không tìm thấy bình luận hoặc bạn không có quyền xóa."
        )

    if comment.is_deleted:
        raise ValidationError("Bình luận này đã được xóa trước đó.")

    comment.is_deleted = True
    comment.content = ""
    comment.save(
        update_fields=["is_deleted", "content", "updated_at"]
    )

    return comment
