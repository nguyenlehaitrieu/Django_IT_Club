
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.core.paginator import Paginator
from django.db.models import F
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import AnnouncementForm
from .models import Announcement


def can_manage_announcements(user):
    if not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    return user.groups.filter(
        name__in=["Admin", "Editor"]
    ).exists()


announcement_manager_required = user_passes_test(
    can_manage_announcements,
    login_url="/login/",
    redirect_field_name="next",
)


def announcement_list_view(request):
    announcement_queryset = (
        Announcement.objects
        .filter(is_published=True)
        .select_related("author")
        .order_by(
            F("published_at").desc(nulls_last=True),
            "-id",
        )
    )

    paginator = Paginator(announcement_queryset, 4)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "announcements": page_obj.object_list,
        "page_obj": page_obj,
        "can_manage_announcements": can_manage_announcements(
            request.user
        ),
    }

    return render(
        request,
        "core/announcements/list.html",
        context,
    )


def announcement_detail_view(request, pk):
    announcement = get_object_or_404(
        Announcement.objects.select_related("author"),
        pk=pk,
        is_published=True,
    )

    return render(
        request,
        "core/announcements/detail.html",
        {
            "announcement": announcement,
            "can_manage_announcements": (
                can_manage_announcements(request.user)
            ),
        },
    )


@announcement_manager_required
def announcement_create_view(request):
    if request.method == "POST":
        form = AnnouncementForm(
            request.POST,
            request.FILES,
        )

        if form.is_valid():
            announcement = form.save(commit=False)
            announcement.author = request.user
            announcement.save()

            messages.success(
                request,
                "Đã tạo thông báo thành công!",
            )
            return redirect("announcement_list")
    else:
        form = AnnouncementForm()

    return render(
        request,
        "core/announcements/form.html",
        {
            "form": form,
            "is_edit": False,
        },
    )


@announcement_manager_required
def announcement_edit_view(request, pk):
    announcement = get_object_or_404(
        Announcement,
        pk=pk,
    )

    if request.method == "POST":
        form = AnnouncementForm(
            request.POST,
            request.FILES,
            instance=announcement,
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Đã cập nhật thông báo thành công!",
            )
            return redirect("announcement_list")
    else:
        form = AnnouncementForm(
            instance=announcement,
        )

    return render(
        request,
        "core/announcements/form.html",
        {
            "form": form,
            "is_edit": True,
            "announcement": announcement,
        },
    )


@announcement_manager_required
@require_POST
def announcement_delete_view(request, pk):
    announcement = get_object_or_404(
        Announcement,
        pk=pk,
    )
    announcement.delete()

    messages.success(
        request,
        "Đã xóa thông báo thành công!",
    )
    return redirect("announcement_list")
