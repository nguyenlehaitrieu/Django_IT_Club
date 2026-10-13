import logging
from urllib.parse import urlparse, parse_qs
from django.db.models import Q, Count

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.core.exceptions import ValidationError, PermissionDenied
from django.core.paginator import Paginator
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from django.db.models import Prefetch
from .models import ForumComment

from .models import (
    ForumTopic,
    ForumTopicImage,
    ForumComment,
    ForumLike,
    ForumReport,
    ForumModerationLog,
)
from .forum_services import (
    like_topic,
    create_comment,
    delete_own_comment,
)


logger = logging.getLogger(__name__)


# =========================================================
# QUYỀN KIỂM DUYỆT
# =========================================================

def can_moderate_forum(user):
    """Admin, Editor hoặc superuser được kiểm duyệt Forum."""
    return (
        user.is_authenticated
        and (
            user.is_superuser
            or user.groups.filter(name__in=["Admin", "Editor"]).exists()
        )
    )


# =========================================================
# GIỚI HẠN TỐC ĐỘ THAO TÁC
# =========================================================

def rate_limit(user, action, limit, window_seconds):
    """Giới hạn số thao tác trong một khoảng thời gian."""
    key = f"forum_rate:{action}:{user.pk}"
    current = cache.get(key, 0)

    if current >= limit:
        return False

    cache.set(key, current + 1, timeout=window_seconds)
    return True


# =========================================================
# KIỂM TRA URL YOUTUBE
# =========================================================

def get_youtube_video_id(url):
    """Lấy ID từ URL YouTube watch, embed, shorts hoặc youtu.be."""
    if not url:
        return ""

    try:
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower()

        if parsed.scheme != "https":
            return ""

        video_id = ""

        if host in {
            "youtube.com",
            "www.youtube.com",
            "m.youtube.com",
        }:
            if parsed.path == "/watch":
                video_id = parse_qs(parsed.query).get("v", [""])[0]

            elif parsed.path.startswith(("/embed/", "/shorts/")):
                parts = parsed.path.strip("/").split("/")
                if len(parts) == 2:
                    video_id = parts[1]

        elif host == "youtu.be":
            parts = parsed.path.strip("/").split("/")
            if len(parts) == 1:
                video_id = parts[0]

        if video_id and all(
            char.isalnum() or char in "-_"
            for char in video_id
        ):
            return video_id

    except (ValueError, IndexError):
        logger.exception("Lỗi phân tích URL YouTube")

    return ""


def is_valid_youtube_url(url):
    """Chấp nhận URL trống hoặc URL YouTube hợp lệ."""
    if not url:
        return True

    return bool(get_youtube_video_id(url))


def get_youtube_embed_url(url):
    """Chuyển URL YouTube thành URL dùng trong iframe."""
    video_id = get_youtube_video_id(url)

    if not video_id:
        return ""

    return f"https://www.youtube.com/embed/{video_id}"


# =========================================================
# QUERYSET FORUM CÔNG KHAI
# =========================================================

def topic_queryset():
    """Chỉ hiển thị bài đã được duyệt."""
    return (
        ForumTopic.objects
        .filter(status="published")
        .select_related("author")
        .prefetch_related("images")
        .order_by("-published_at", "-created_at")
    )


# =========================================================
# DANH SÁCH BÀI VIẾT
# =========================================================

def forum_list_view(request):
    topics = topic_queryset()

    category = request.GET.get("category", "").strip()
    valid_categories = {
        choice[0] for choice in ForumTopic.CATEGORY_CHOICES
    }

    if category in valid_categories:
        topics = topics.filter(category=category)

    query = request.GET.get("q", "").strip()

    if query:
        topics = topics.filter(title__icontains=query)

    paginator = Paginator(topics, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(
        request,
        "core/forum/list.html",
        {
            "page_obj": page_obj,
            "topics": page_obj.object_list,
            "categories": ForumTopic.CATEGORY_CHOICES,
            "selected_category": category,
            "search_query": query,
            "can_moderate_forum": can_moderate_forum(request.user),
        },
    )


# =========================================================
# CHI TIẾT BÀI VIẾT
# =========================================================

def forum_detail_view(request, pk):
    topic = get_object_or_404(topic_queryset(), pk=pk)
    comments_queryset = (
        topic.comments
        .filter(
            status="published",
            parent__isnull=True,
        )
        .select_related("author")
        .order_by("created_at")
    )
    comments_paginator = Paginator(comments_queryset, 10)
    comments_page = comments_paginator.get_page(request.GET.get("comment_page"))
    liked = False
    if request.user.is_authenticated:
        liked = ForumLike.objects.filter(
            topic=topic,
            user=request.user,
        ).exists()
    video_embed_url = get_youtube_embed_url(topic.video_url)
    return render(
        request,
        "core/forum/detail.html",
        {
            "topic": topic,
            "comments": comments_page.object_list,
            "comments_page": comments_page,
            "liked": liked,
            "can_moderate_forum": can_moderate_forum(request.user),
            "video_embed_url": video_embed_url,
        },
    )

    topic = get_object_or_404(topic_queryset(), pk=pk)

    comments = (
        topic.comments
        .filter(
            status="published",
            parent__isnull=True,
        )
        .select_related("author")
        .prefetch_related(
            Prefetch(
                "replies",
                queryset=(
                    ForumComment.objects
                    .filter(status="published")
                    .select_related("author")
                    .order_by("created_at")
                ),
            )
        )
        .order_by("created_at")
    )


    liked = False

    if request.user.is_authenticated:
        liked = ForumLike.objects.filter(
            topic=topic,
            user=request.user,
        ).exists()

    video_embed_url = get_youtube_embed_url(topic.video_url)

    return render(
        request,
        "core/forum/detail.html",
        {
            "topic": topic,
            "comments": comments,
            "liked": liked,
            "can_moderate_forum": can_moderate_forum(request.user),
            "video_embed_url": video_embed_url,
        },
    )


# =========================================================
# TẠO BÀI VIẾT
# Bài mới luôn ở trạng thái pending để chờ duyệt.
# =========================================================

@login_required
def forum_create_view(request):
    logger.info(
        "Forum create view: method=%s user_id=%s",
        request.method,
        request.user.pk,
    )

    if request.method != "POST":
        return render(
            request,
            "core/forum/create.html",
            {"categories": ForumTopic.CATEGORY_CHOICES},
        )

    # Giới hạn 3 lần gửi trong 10 phút.
    if not rate_limit(request.user, "topic", 3, 600):
        logger.warning(
            "Forum create bị rate limit: user_id=%s",
            request.user.pk,
        )
        messages.error(
            request,
            "Bạn đăng chủ đề quá nhanh. Vui lòng thử lại sau.",
        )
        return redirect("forum_create")

    title = request.POST.get("title", "").strip()
    content = request.POST.get("content", "").strip()
    category = request.POST.get("category", "discussion").strip()
    video_url = request.POST.get("video_url", "").strip()
    uploaded_images = request.FILES.getlist("images")

    logger.info(
        "Forum create nhận dữ liệu: user_id=%s category=%s "
        "image_count=%s has_video=%s",
        request.user.pk,
        category,
        len(uploaded_images),
        bool(video_url),
    )

    valid_categories = {
        choice[0] for choice in ForumTopic.CATEGORY_CHOICES
    }

    errors = []

    # Kiểm tra tiêu đề.
    if not title or len(title) > 200:
        errors.append("Tiêu đề phải có từ 1 đến 200 ký tự.")

    # Kiểm tra nội dung.
    if not content or len(content) > 20000:
        errors.append("Nội dung phải có từ 1 đến 20000 ký tự.")

    # Kiểm tra danh mục.
    if category not in valid_categories:
        errors.append("Danh mục không hợp lệ.")

    # Kiểm tra số lượng ảnh.
    if len(uploaded_images) > 4:
        errors.append("Mỗi chủ đề chỉ được đính kèm tối đa 4 ảnh.")

    # Kiểm tra dung lượng và định dạng ảnh.
    for image in uploaded_images:
        if image.size > 5 * 1024 * 1024:
            errors.append(
                f"Ảnh '{image.name}' vượt quá giới hạn 5 MB."
            )
            continue

        if image.content_type not in {
            "image/jpeg",
            "image/png",
            "image/webp",
        }:
            errors.append(
                f"Ảnh '{image.name}' phải là JPG, PNG hoặc WebP."
            )
            continue

        try:
            from PIL import Image

            with Image.open(image) as img:
                if img.format not in {"JPEG", "PNG", "WEBP"}:
                    errors.append(
                        f"Ảnh '{image.name}' không đúng định dạng hỗ trợ."
                    )
                else:
                    img.verify()

        except Exception:
            errors.append(
                f"File '{image.name}' không phải ảnh hợp lệ."
            )

        finally:
            image.seek(0)

    # Kiểm tra URL video.
    if video_url and not is_valid_youtube_url(video_url):
        errors.append("Vui lòng nhập đường dẫn YouTube hợp lệ.")

    # Dữ liệu không hợp lệ.
    if errors:
        logger.warning(
            "Forum create validation failed: user_id=%s errors=%s",
            request.user.pk,
            errors,
        )

        for error in errors:
            messages.error(request, error)

        return redirect("forum_create")

    # Chặn tiêu đề trùng của cùng tài khoản trong 24 giờ.
    duplicate = ForumTopic.objects.filter(
        author=request.user,
        created_at__gte=timezone.now() - timezone.timedelta(hours=24),
        title__iexact=title,
    ).exists()

    if duplicate:
        logger.warning(
            "Forum create trùng tiêu đề: user_id=%s title=%s",
            request.user.pk,
            title,
        )
        messages.error(
            request,
            "Bạn đã tạo chủ đề có tiêu đề này gần đây.",
        )
        return redirect("forum_create")

    # Lưu chủ đề và ảnh trong transaction.
    try:
        with transaction.atomic():
            topic = ForumTopic.objects.create(
                author=request.user,
                title=title,
                content=content,
                category=category,
                video_url=video_url,
                status="pending",
            )

            for image in uploaded_images:
                ForumTopicImage.objects.create(
                    topic=topic,
                    image=image,
                )

    except Exception:
        logger.exception(
            "Không thể lưu chủ đề Forum: user_id=%s",
            request.user.pk,
        )

        messages.error(
            request,
            "Không thể lưu chủ đề. Vui lòng thử lại.",
        )
        return redirect("forum_create")

    logger.info(
        "Forum create thành công: topic_id=%s status=%s",
        topic.pk,
        topic.status,
    )

    messages.success(
        request,
        "Chủ đề đã được gửi và đang chờ quản trị viên duyệt.",
    )

    return redirect("forum_list")


# =========================================================
# THÍCH BÀI VIẾT
# =========================================================

@login_required
@require_POST
def forum_like_view(request, pk):
    try:
        success, message = like_topic(request.user, pk)

    except ValidationError as exc:
        messages.error(request, "; ".join(exc.messages))

    else:
        if success:
            messages.success(request, message)
        else:
            messages.info(request, message)

    return redirect("forum_detail", pk=pk)


# =========================================================
# BÌNH LUẬN
# =========================================================

@login_required
@require_POST
def forum_comment_view(request, pk):
    if not rate_limit(request.user, "comment", 5, 60):
        messages.error(
            request,
            "Bạn bình luận quá nhanh. Vui lòng thử lại sau.",
        )
        return redirect("forum_detail", pk=pk)

    content = request.POST.get("content", "").strip()
    parent_id = request.POST.get("parent_id", "").strip()

    try:
        create_comment(
            request.user,
            pk,
            content,
            parent_id=parent_id or None,
        )

    except ValidationError as exc:
        messages.error(request, "; ".join(exc.messages))

    else:
        messages.success(
            request,
            "Đã gửi phản hồi thành công!"
            if parent_id
            else "Đã gửi bình luận thành công!",
        )

    return redirect("forum_detail", pk=pk)


# =========================================================
# BÁO CÁO BÀI VIẾT
# =========================================================

@login_required
@require_POST
def forum_report_view(request, pk):
    topic = get_object_or_404(
        ForumTopic,
        pk=pk,
        status="published",
    )

    reason = request.POST.get("reason", "").strip()
    details = request.POST.get("details", "").strip()

    valid_reasons = {
        choice[0] for choice in ForumReport.REASON_CHOICES
    }

    if reason not in valid_reasons:
        messages.error(request, "Lý do báo cáo không hợp lệ.")
        return redirect("forum_detail", pk=pk)

    if topic.author_id == request.user.pk:
        messages.error(
            request,
            "Bạn không thể báo cáo chủ đề của chính mình.",
        )
        return redirect("forum_detail", pk=pk)

    existing = ForumReport.objects.filter(
        reporter=request.user,
        topic=topic,
        comment__isnull=True,
        status="pending",
    ).exists()

    if existing:
        messages.info(request, "Bạn đã báo cáo chủ đề này.")
        return redirect("forum_detail", pk=pk)

    ForumReport.objects.create(
        reporter=request.user,
        topic=topic,
        reason=reason,
        details=details[:500],
    )

    messages.success(
        request,
        "Đã gửi báo cáo. Quản trị viên sẽ kiểm tra nội dung.",
    )

    return redirect("forum_detail", pk=pk)


# =========================================================
# KIỂM DUYỆT BÀI VIẾT
# =========================================================

@login_required
@require_POST
def forum_moderate_topic_view(request, pk):
    if not can_moderate_forum(request.user):
        raise PermissionDenied(
            "Bạn không có quyền kiểm duyệt diễn đàn."
        )

    topic = get_object_or_404(ForumTopic, pk=pk)
    action = request.POST.get("action", "").strip()
    note = request.POST.get("note", "").strip()[:500]

    status_map = {
        "approve": "published",
        "hide": "hidden",
        "reject": "rejected",
        "restore": "published",
    }

    if action not in status_map:
        messages.error(
            request,
            "Hành động kiểm duyệt không hợp lệ.",
        )
        return redirect("forum_list")

    with transaction.atomic():
        topic.status = status_map[action]

        if action in {"approve", "restore"}:
            if topic.published_at is None:
                topic.published_at = timezone.now()

        topic.save(
            update_fields=[
                "status",
                "published_at",
                "updated_at",
            ]
        )

        ForumModerationLog.objects.create(
            moderator=request.user,
            topic=topic,
            action=action,
            note=note,
        )

    messages.success(
        request,
        "Đã cập nhật trạng thái chủ đề.",
    )

    return redirect("forum_list")


# =========================================================
# HÀNG CHỜ DUYỆT
# =========================================================

@login_required
def forum_moderation_queue_view(request):
    if not can_moderate_forum(request.user):
        raise PermissionDenied(
            "Bạn không có quyền truy cập hàng chờ duyệt."
        )

    topics = (
        ForumTopic.objects
        .filter(status="pending")
        .select_related("author")
        .prefetch_related("images")
        .order_by("created_at")
    )

    paginator = Paginator(topics, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(
        request,
        "core/forum/moderation_queue.html",
        {
            "page_obj": page_obj,
            "topics": page_obj.object_list,
        },
    )



# =========================================================
# ADMIN QUẢN LÝ TẤT CẢ TOPIC
# =========================================================

def can_manage_forum(user):
    """Chỉ Admin hoặc superuser được quản lý và xóa topic."""
    return (
        user.is_authenticated
        and (
            user.is_superuser
            or user.groups.filter(name="Admin").exists()
        )
    )


@login_required
def forum_manage_view(request):
    if not can_manage_forum(request.user):
        raise PermissionDenied(
            "Bạn không có quyền quản lý diễn đàn."
        )

    topics = (
        ForumTopic.objects
        .select_related("author")
        .prefetch_related("images")
        .annotate(
            total_comments=Count("comments", distinct=True),
            total_likes=Count("likes", distinct=True),
            total_reports=Count("reports", distinct=True),
        )
        .order_by("-created_at")
    )

    # Tìm kiếm theo tiêu đề, nội dung hoặc tên tài khoản.
    query = request.GET.get("q", "").strip()
    if query:
        topics = topics.filter(
            Q(title__icontains=query)
            | Q(content__icontains=query)
            | Q(author__username__icontains=query)
        )

    # Lọc trạng thái.
    status = request.GET.get("status", "").strip()
    valid_statuses = {
        value for value, label in ForumTopic.STATUS_CHOICES
    }

    if status in valid_statuses:
        topics = topics.filter(status=status)

    # Lọc danh mục.
    category = request.GET.get("category", "").strip()
    valid_categories = {
        value for value, label in ForumTopic.CATEGORY_CHOICES
    }

    if category in valid_categories:
        topics = topics.filter(category=category)

    # Thống kê toàn bộ topic, không phụ thuộc bộ lọc.
    all_topics = ForumTopic.objects.all()

    stats = {
        "total": all_topics.count(),
        "pending": all_topics.filter(status="pending").count(),
        "published": all_topics.filter(status="published").count(),
        "hidden": all_topics.filter(status="hidden").count(),
        "rejected": all_topics.filter(status="rejected").count(),
    }

    paginator = Paginator(topics, 15)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(
        request,
        "core/forum/manage.html",
        {
            "page_obj": page_obj,
            "topics": page_obj.object_list,
            "stats": stats,
            "search_query": query,
            "selected_status": status,
            "selected_category": category,
            "status_choices": ForumTopic.STATUS_CHOICES,
            "category_choices": ForumTopic.CATEGORY_CHOICES,
        },
    )


@login_required
@require_POST
def forum_delete_topic_view(request, pk):
    if not can_manage_forum(request.user):
        raise PermissionDenied(
            "Chỉ Admin mới có quyền xóa chủ đề."
        )

    topic = get_object_or_404(
        ForumTopic.objects.prefetch_related("images"),
        pk=pk,
    )

    title = topic.title

    # Lưu đường dẫn file trước khi xóa các bản ghi trong database.
    image_files = [
        image.image
        for image in topic.images.all()
        if image.image
    ]

    topic.delete()

    # Xóa file vật lý để tránh lưu lại ảnh không còn được sử dụng.
    for image_file in image_files:
        try:
            image_file.storage.delete(image_file.name)
        except Exception:
            logger.exception(
                "Không thể xóa file ảnh của topic #%s",
                pk,
            )

    messages.success(
        request,
        f'Đã xóa vĩnh viễn chủ đề "{title}".',
    )

    return redirect("forum_manage")


@login_required
def forum_edit_topic_view(request, pk):
    """Chỉ Admin hoặc superuser được chỉnh sửa topic."""
    if not can_manage_forum(request.user):
        raise PermissionDenied("Chỉ Admin mới có quyền chỉnh sửa chủ đề.")
    topic = get_object_or_404(
        ForumTopic.objects.prefetch_related("images"),
        pk=pk,
    )
    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        content = request.POST.get("content", "").strip()
        category = request.POST.get("category", "").strip()
        video_url = request.POST.get("video_url", "").strip()
        uploaded_images = request.FILES.getlist("images")
        valid_categories = {value for value, label in ForumTopic.CATEGORY_CHOICES}
        errors = []
        if not title or len(title) > 200:
            errors.append("Tiêu đề phải có từ 1 đến 200 ký tự.")
        if not content or len(content) > 20000:
            errors.append("Nội dung phải có từ 1 đến 20000 ký tự.")
        if category not in valid_categories:
            errors.append("Danh mục không hợp lệ.")
        if video_url and not is_valid_youtube_url(video_url):
            errors.append("Vui lòng nhập đường dẫn YouTube hợp lệ.")
        existing_images = list(topic.images.all())
        if len(existing_images) + len(uploaded_images) > 4:
            errors.append("Mỗi chủ đề chỉ được đính kèm tối đa 4 ảnh.")
        for image in uploaded_images:
            if image.size > 5 * 1024 * 1024:
                errors.append(f"Ảnh '{image.name}' vượt quá giới hạn 5 MB.")
                continue
            if image.content_type not in {"image/jpeg", "image/png", "image/webp"}:
                errors.append(f"Ảnh '{image.name}' phải là JPG, PNG hoặc WebP.")
                continue
            try:
                from PIL import Image
                with Image.open(image) as img:
                    if img.format not in {"JPEG", "PNG", "WEBP"}:
                        errors.append(f"Ảnh '{image.name}' không đúng định dạng hỗ trợ.")
                    else:
                        img.verify()
            except Exception:
                errors.append(f"File '{image.name}' không phải ảnh hợp lệ.")
            finally:
                image.seek(0)
        if errors:
            for error in errors:
                messages.error(request, error)
            return redirect("forum_edit_topic", pk=topic.pk)
        with transaction.atomic():
            topic.title = title
            topic.content = content
            topic.category = category
            topic.video_url = video_url
            topic.save(update_fields=[
                "title",
                "content",
                "category",
                "video_url",
                "updated_at",
            ])
            for image in uploaded_images:
                ForumTopicImage.objects.create(topic=topic, image=image)
        messages.success(request, "Đã cập nhật chủ đề thành công.")
        return redirect("forum_manage")
    return render(
        request,
        "core/forum/edit.html",
        {
            "topic": topic,
            "categories": ForumTopic.CATEGORY_CHOICES,
        },
    )




@login_required
@require_POST
def forum_delete_comment_view(request, pk, comment_id):
    """Cho phép người dùng xóa mềm bình luận của chính mình."""
    if not rate_limit(request.user, "delete_comment", 5, 60):
        messages.error(
            request,
            "Bạn thao tác quá nhanh. Vui lòng thử lại sau.",
        )
        return redirect("forum_detail", pk=pk)

    try:
        delete_own_comment(
            request.user,
            comment_id,
            topic_id=pk,
        )
    except ValidationError as exc:
        messages.error(request, "; ".join(exc.messages))
    else:
        messages.success(request, "Đã xóa bình luận thành công!")

    return redirect("forum_detail", pk=pk)



