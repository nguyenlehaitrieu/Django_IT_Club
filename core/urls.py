
from django.urls import path
from . import views
from . import announcement_views
from . import forum_views

from core.views import (
    developer_space_view,
    unlock_profile_theme,
    equip_profile_theme,
)


urlpatterns = [
    path("", views.home, name="home"),

    # Authentication
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    # Profile
    path("profile/", views.profile_view, name="profile"),
    path("profile/edit/", views.profile_edit_view, name="profile_edit"),
    path(
        "members/<str:username>/",
        views.public_member_profile_view,
        name="public_member_profile",
    ),

    # Admin dashboard
    path(
        "admin-dashboard/",
        views.admin_dashboard,
        name="admin_dashboard",
    ),
    path(
        "admin-dashboard/members/<int:user_id>/role/",
        views.change_member_role,
        name="change_member_role",
    ),
    path(
        "admin-dashboard/members/<int:user_id>/status/",
        views.toggle_member_status,
        name="toggle_member_status",
    ),

    # Developer space
    path(
        "developer-space/",
        developer_space_view,
        name="developer_space",
    ),
    path(
        "developer-space/unlock/<int:theme_id>/",
        unlock_profile_theme,
        name="unlock_profile_theme",
    ),
    path(
        "developer-space/equip/<int:theme_id>/",
        equip_profile_theme,
        name="equip_profile_theme",
    ),

    # Member posts
    path(
        "profile/posts/",
        views.member_post_list_view,
        name="member_post_list",
    ),
    path(
        "profile/posts/create/",
        views.member_post_create_view,
        name="member_post_create",
    ),
    path(
        "profile/posts/<int:pk>/publish/",
        views.member_post_publish_view,
        name="member_post_publish",
    ),
    path(
        "profile/posts/<int:pk>/edit/",
        views.member_post_edit_view,
        name="member_post_edit",
    ),

    
    # Announcements - Trang thông báo riêng
    path(
        "announcements/",
        announcement_views.announcement_list_view,
        name="announcement_list",
    ),
    path(
        "announcements/",
        announcement_views.announcement_list_view,
        name="announcements",
    ),
    path(
        "announcements/create/",
        announcement_views.announcement_create_view,
        name="announcement_create",
    ),
    path(
        "announcements/<int:pk>/edit/",
        announcement_views.announcement_edit_view,
        name="announcement_edit",
    ),
    path(
        "announcements/<int:pk>/delete/",
        announcement_views.announcement_delete_view,
        name="announcement_delete",
    ),
    path(
        "announcements/<int:pk>/",
        announcement_views.announcement_detail_view,
        name="announcement_detail",
    ),



# Forum
    path(
        "forum/",
        forum_views.forum_list_view,
        name="forum_list",
    ),
    path(
        "forum/create/",
        forum_views.forum_create_view,
        name="forum_create",
    ),
    path(
        "forum/moderation/",
        forum_views.forum_moderation_queue_view,
        name="forum_moderation_queue",
    ),
    path(
        "forum/<int:pk>/like/",
        forum_views.forum_like_view,
        name="forum_like",
    ),
    path(
        "forum/<int:pk>/comment/",
        forum_views.forum_comment_view,
        name="forum_comment",
    ),
    path(
        "forum/<int:pk>/report/",
        forum_views.forum_report_view,
        name="forum_report",
    ),
    path(
        "forum/<int:pk>/moderate/",
        forum_views.forum_moderate_topic_view,
        name="forum_moderate_topic",
    ),
    path(
        "forum/<int:pk>/",
        forum_views.forum_detail_view,
        name="forum_detail",
    ),

    # Forum Admin Management
    path(
        "forum/manage/",
        forum_views.forum_manage_view,
        name="forum_manage",
    ),
    path(
        "forum/<int:pk>/edit/",
        forum_views.forum_edit_topic_view,
        name="forum_edit_topic",
    ),
    path(
        "forum/<int:pk>/delete/",
        forum_views.forum_delete_topic_view,
        name="forum_delete_topic",
    ),

    path(
        "forum/<int:pk>/edit/",
        forum_views.forum_edit_topic_view,
        name="forum_edit_topic",
    ),


]



