from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import (
    authenticate,
    login,
    logout,
)
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib.auth.models import Group, User
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.utils.http import url_has_allowed_host_and_scheme

from .forms import ProfileUpdateForm, MemberProfileForm, MemberPostForm, AnnouncementForm
from .models import MemberProfile, ProfileTheme, MemberPost, Announcement
from .services import unlock_theme, equip_theme
from .decorators import role_required




# =========================================================
# HÀM HỖ TRỢ PHÂN QUYỀN
# =========================================================

def is_admin_user(user):
    """Superuser hoặc người thuộc nhóm Admin."""
    return (
        user.is_authenticated
        and (
            user.is_superuser
            or user.groups.filter(name="Admin").exists()
        )
    )


# =========================================================
# TRANG CHỦ
# =========================================================

def home(request):
    return render(request, "core/index.html")


# =========================================================
# ĐĂNG KÝ
# =========================================================

def register_view(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        form = UserCreationForm(request.POST)

        if form.is_valid():
            user = form.save()

            member_group, _ = Group.objects.get_or_create(
                name="Member"
            )
            user.groups.add(member_group)

            login(request, user)

            messages.success(
                request,
                "Đăng ký tài khoản thành công! "
                "Chào mừng bạn đến với IT MUCE."
            )
            return redirect("home")
    else:
        form = UserCreationForm()

    return render(
        request,
        "core/accounts/register.html",
        {"form": form},
    )


# =========================================================
# ĐĂNG NHẬP
# =========================================================

def login_view(request):
    if request.user.is_authenticated:
        return redirect("home")

    next_url = request.POST.get("next") or request.GET.get("next", "")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        user = authenticate(
            request,
            username=username,
            password=password,
        )

        if user is not None:
            login(request, user)

            # Chỉ chuyển hướng đến URL nội bộ hợp lệ.
            if next_url and url_has_allowed_host_and_scheme(
                next_url,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            ):
                return redirect(next_url)

            return redirect("home")

        messages.error(
            request,
            "Tên đăng nhập hoặc mật khẩu không chính xác."
        )

    return render(
        request,
        "core/accounts/login.html",
        {"next": next_url},
    )


# =========================================================
# ĐĂNG XUẤT
# =========================================================

@login_required
@require_POST
def logout_view(request):
    logout(request)
    messages.success(request, "Bạn đã đăng xuất thành công.")
    return redirect("home")


# =========================================================
# HỒ SƠ CÁ NHÂN
# =========================================================

@login_required
def profile_edit_view(request):
    profile, _ = MemberProfile.objects.get_or_create(
        user=request.user
    )
    user = request.user

    if request.method == "POST":
        account_form = ProfileUpdateForm(
            request.POST,
            instance=user,
            prefix="account",
        )

        profile_form = MemberProfileForm(
            request.POST,
            request.FILES,
            instance=profile,
            prefix="profile",
        )

        if account_form.is_valid() and profile_form.is_valid():
            account_form.save()
            profile_form.save()

            messages.success(
                request,
                "Cập nhật hồ sơ thành công!"
            )
            return redirect("profile")

        messages.error(
            request,
            "Có lỗi khi cập nhật. "
            "Vui lòng kiểm tra các trường bên dưới."
        )

    else:
        account_form = ProfileUpdateForm(
            instance=user,
            prefix="account",
        )

        profile_form = MemberProfileForm(
            instance=profile,
            prefix="profile",
        )

    # Xác định vai trò ưu tiên.
    if user.is_superuser:
        role = "Admin"
    else:
        role_names = list(
            user.groups.values_list("name", flat=True)
        )
        priority = ["Admin", "Editor", "Member"]

        role = next(
            (name for name in priority if name in role_names),
            "Chưa phân nhóm",
        )

    # Tính mức độ hoàn thiện hồ sơ: 9 mục.
    profile_fields = [
        bool(user.first_name.strip()),
        bool(user.last_name.strip()),
        bool(user.email.strip()),
        bool(profile.avatar),
        bool(profile.bio.strip()),
        bool(profile.interests),
        bool(profile.skills.strip()),
        bool(profile.github_url.strip()),
        bool(profile.portfolio_url.strip()),
    ]

    profile_completion = round(
        sum(profile_fields) / len(profile_fields) * 100
    )

    return render(
        request,
        "core/accounts/profile.html",
        {
            "account_form": account_form,
            "profile_form": profile_form,
            "profile_role": role,
            "profile": profile,
            "profile_completion": profile_completion,
        },
    )


# =========================================================
# KIỂM TRA QUYỀN ADMIN DASHBOARD
# =========================================================

@login_required
def admin_dashboard(request):
    if not is_admin_user(request.user):
        raise PermissionDenied(
            "Bạn không có quyền truy cập trang quản trị."
        )

    total_users = User.objects.count()

    member_count = User.objects.filter(
        groups__name="Member"
    ).distinct().count()

    editor_count = User.objects.filter(
        groups__name="Editor"
    ).distinct().count()

    admin_count = User.objects.filter(
        groups__name="Admin"
    ).distinct().count()

    users = User.objects.prefetch_related("groups").order_by(
        "-date_joined"
    )

    # Tìm kiếm username, email hoặc họ tên.
    search_query = request.GET.get("q", "").strip()

    if search_query:
        users = users.filter(
            Q(username__icontains=search_query)
            | Q(email__icontains=search_query)
            | Q(first_name__icontains=search_query)
            | Q(last_name__icontains=search_query)
        ).distinct()

    # Lọc theo vai trò.
    role_filter = request.GET.get("role", "").strip()

    if role_filter in ["Member", "Editor", "Admin"]:
        users = users.filter(
            groups__name=role_filter
        ).distinct()

    elif role_filter == "Superuser":
        users = users.filter(is_superuser=True)

    elif role_filter == "Unassigned":
        users = users.filter(groups__isnull=True)

    return render(
        request,
        "core/admin/dashboard.html",
        {
            "total_users": total_users,
            "member_count": member_count,
            "editor_count": editor_count,
            "admin_count": admin_count,
            "users": users,
            "search_query": search_query,
            "role_filter": role_filter,
        },
    )


# =========================================================
# THAY ĐỔI VAI TRÒ THÀNH VIÊN
# =========================================================

@login_required
@require_POST
def change_member_role(request, user_id):
    current_user = request.user

    if not is_admin_user(current_user):
        raise PermissionDenied(
            "Bạn không có quyền quản lý vai trò."
        )

    target_user = get_object_or_404(User, pk=user_id)

    # Không thay đổi vai trò superuser.
    if target_user.is_superuser:
        messages.error(
            request,
            "Không thể thay đổi vai trò của superuser tại đây."
        )
        return redirect("admin_dashboard")

    # Không cho tự thay đổi vai trò của chính mình.
    if target_user.pk == current_user.pk:
        messages.error(
            request,
            "Bạn không thể tự thay đổi vai trò của mình."
        )
        return redirect("admin_dashboard")

    role = request.POST.get("role", "").strip()

    if role not in ["Member", "Editor", "Admin"]:
        messages.error(request, "Vai trò không hợp lệ.")
        return redirect("admin_dashboard")

    # Chỉ superuser được cấp vai trò Admin.
    if not current_user.is_superuser and role == "Admin":
        messages.error(
            request,
            "Chỉ superuser mới được cấp vai trò Admin."
        )
        return redirect("admin_dashboard")

    target_group, _ = Group.objects.get_or_create(name=role)

    managed_groups = Group.objects.filter(
        name__in=["Member", "Editor", "Admin"]
    )

    target_user.groups.remove(*managed_groups)
    target_user.groups.add(target_group)

    messages.success(
        request,
        f"Đã cập nhật vai trò của {target_user.username} "
        f"thành {role}."
    )
    return redirect("admin_dashboard")


# =========================================================
# KHÓA / MỞ KHÓA TÀI KHOẢN
# =========================================================

@login_required
@require_POST
def toggle_member_status(request, user_id):
    current_user = request.user

    if not is_admin_user(current_user):
        raise PermissionDenied(
            "Bạn không có quyền quản lý tài khoản."
        )

    target_user = get_object_or_404(User, pk=user_id)

    # Không khóa hoặc mở khóa superuser.
    if target_user.is_superuser:
        messages.error(
            request,
            "Không thể thay đổi trạng thái superuser tại đây."
        )
        return redirect("admin_dashboard")

    # Không cho tự khóa tài khoản đang sử dụng.
    if target_user.pk == current_user.pk:
        messages.error(
            request,
            "Bạn không thể khóa hoặc mở khóa chính tài khoản của mình."
        )
        return redirect("admin_dashboard")

    target_user.is_active = not target_user.is_active
    target_user.save(update_fields=["is_active"])

    if target_user.is_active:
        messages.success(
            request,
            f"Đã mở khóa tài khoản {target_user.username}."
        )
    else:
        messages.success(
            request,
            f"Đã khóa tài khoản {target_user.username}."
        )

    return redirect("admin_dashboard")


# =========================================================
# DEVELOPER SPACE
# =========================================================

@login_required
def developer_space_view(request):
    profile, _ = MemberProfile.objects.get_or_create(
        user=request.user
    )

    # Theme mặc định miễn phí.
    default_theme = ProfileTheme.objects.filter(
        slug="cyber-blue",
        is_active=True,
    ).first()

    if default_theme:
        profile.unlocked_themes.add(default_theme)

        if profile.active_theme_id is None:
            profile.active_theme = default_theme
            profile.save(
                update_fields=["active_theme", "updated_at"]
            )

    themes = ProfileTheme.objects.filter(is_active=True)

    unlocked_theme_ids = list(
        profile.unlocked_themes.values_list("id", flat=True)
    )

    is_admin = is_admin_user(request.user)

    return render(
        request,
        "core/developer_space.html",
        {
            "profile": profile,
            "themes": themes,
            "unlocked_theme_ids": unlocked_theme_ids,
            "is_admin": is_admin,
        },
    )


# =========================================================
# MỞ KHÓA THEME
# =========================================================

@login_required
@require_POST
def unlock_profile_theme(request, theme_id):
    profile, _ = MemberProfile.objects.get_or_create(
        user=request.user
    )

    is_admin = is_admin_user(request.user)

    try:
        success, message = unlock_theme(
            profile.pk,
            theme_id,
            is_admin=is_admin,
        )
    except ProfileTheme.DoesNotExist:
        messages.error(
            request,
            "Theme không tồn tại hoặc đã ngừng hoạt động."
        )
        return redirect("developer_space")

    if success:
        messages.success(request, message)
    else:
        messages.warning(request, message)

    return redirect("developer_space")


# =========================================================
# TRANG BỊ THEME
# =========================================================

@login_required
@require_POST
def equip_profile_theme(request, theme_id):
    profile, _ = MemberProfile.objects.get_or_create(
        user=request.user
    )

    is_admin = is_admin_user(request.user)

    try:
        success, message = equip_theme(
            profile.pk,
            theme_id,
            is_admin=is_admin,
        )
    except ProfileTheme.DoesNotExist:
        messages.error(
            request,
            "Theme không tồn tại hoặc đã ngừng hoạt động."
        )
        return redirect("developer_space")

    if success:
        messages.success(request, message)
    else:
        messages.warning(request, message)

    return redirect("developer_space")

# =========================================================
# PROFILE
# =========================================================
def profile_view(request):
    """Hiển thị hồ sơ công khai của người đang đăng nhập."""
    if request.user.is_authenticated:
        username = request.user.username
        return redirect(
            "public_member_profile",
            username=username,
        )

    # Khách chưa đăng nhập được chuyển đến trang đăng nhập.
    return redirect("login")


# =========================================================
# PROFILE EDIT
# =========================================================
def public_member_profile_view(request, username):
    """Hiển thị hồ sơ công khai của một thành viên."""
    from django.contrib.auth.models import User

    member = get_object_or_404(
        User,
        username=username,
        is_active=True,
    )

    profile, _ = MemberProfile.objects.get_or_create(
        user=member
    )

    role_priority = ["Admin", "Editor", "Member"]

    if member.is_superuser:
        profile_role = "Admin"
    else:
        member_groups = set(
            member.groups.values_list("name", flat=True)
        )
        profile_role = next(
            (
                role for role in role_priority
                if role in member_groups
            ),
            "Member",
        )

    is_owner = (
        request.user.is_authenticated
        and request.user.pk == member.pk
    )

    return render(
        request,
        "core/accounts/public_profile.html",
        {
            "member": member,
            "profile": profile,
            "profile_role": profile_role,
            "is_owner": is_owner,
        },
    )


def profile_view(request):
    """Chuyển đến hồ sơ công khai của thành viên đang đăng nhập."""
    if request.user.is_authenticated:
        return redirect(
            "public_member_profile",
            username=request.user.username,
        )

    return redirect("login")



def public_member_profile_view(request, username):
    """Hiển thị hồ sơ công khai của một thành viên."""
    member = get_object_or_404(
        User,
        username=username,
        is_active=True,
    )

    profile, _ = MemberProfile.objects.get_or_create(
        user=member
    )

    # Xác định vai trò thành viên
    role_priority = ["Admin", "Editor", "Member"]

    if member.is_superuser:
        profile_role = "Admin"
    else:
        member_groups = set(
            member.groups.values_list("name", flat=True)
        )
        profile_role = next(
            (
                role for role in role_priority
                if role in member_groups
            ),
            "Member",
        )

    # Kiểm tra người đang xem có phải chủ hồ sơ không
    is_owner = (
        request.user.is_authenticated
        and request.user.pk == member.pk
    )

    # Lấy các bài viết đã đăng công khai của thành viên
    posts = MemberPost.objects.filter(
        author=member,
        status="published",
    ).order_by("-created_at")

    return render(
        request,
        "core/accounts/public_profile.html",
        {
            "member": member,
            "profile": profile,
            "profile_role": profile_role,
            "is_owner": is_owner,
            "posts": posts,
        },
    )

    """Hiển thị hồ sơ công khai của một thành viên."""
    member = get_object_or_404(
        User,
        username=username,
        is_active=True,
    )

    profile, _ = MemberProfile.objects.get_or_create(
        user=member
    )

    role_priority = ["Admin", "Editor", "Member"]

    if member.is_superuser:
        profile_role = "Admin"
    else:
        member_groups = set(
            member.groups.values_list("name", flat=True)
        )
        profile_role = next(
            (
                role for role in role_priority
                if role in member_groups
            ),
            "Member",
        )

    is_owner = (
        request.user.is_authenticated
        and request.user.pk == member.pk
    )

    return render(
        request,
        "core/accounts/public_profile.html",
        {
            "member": member,
            "profile": profile,
            "profile_role": profile_role,
            "is_owner": is_owner,
        },
    )



# =========================================================
# PROFILE POST 
# =========================================================
@login_required
def member_post_create_view(request):
    if request.method == "POST":
        form = MemberPostForm(
            request.POST,
            request.FILES,
        )

        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user

            # Mặc định lưu nháp để tránh đăng công khai ngoài ý muốn.
            post.status = "draft"
            post.save()

            messages.success(
                request,
                "Đã lưu bài viết thành công!",
            )

            return redirect("member_post_list")
    else:
        form = MemberPostForm()

    return render(
        request,
        "core/accounts/post_form.html",
        {"form": form},
    )



@login_required
def member_post_edit_view(request, pk):
    post = get_object_or_404(
        MemberPost,
        pk=pk,
        author=request.user,
    )

    if request.method == "POST":
        form = MemberPostForm(
            request.POST,
            request.FILES,
            instance=post,
        )

        if form.is_valid():
            form.save()
            messages.success(
                request,
                "Đã cập nhật dự án thành công!",
            )
            return redirect("member_post_list")
    else:
        form = MemberPostForm(instance=post)

    return render(
        request,
        "core/accounts/post_form.html",
        {
            "form": form,
            "post": post,
            "is_edit": True,
        },
    )



@login_required
def member_post_list_view(request):
    posts = MemberPost.objects.filter(
        author=request.user
    ).order_by("-created_at")

    return render(
        request,
        "core/accounts/post_list.html",
        {"posts": posts},
    )


@login_required
@require_POST
def member_post_publish_view(request, pk):
    post = get_object_or_404(
        MemberPost,
        pk=pk,
        author=request.user,
    )

    post.status = "published"
    post.save(update_fields=["status", "updated_at"])

    messages.success(
        request,
        "Bài viết đã được đăng công khai!"
    )

    return redirect("member_post_list")






