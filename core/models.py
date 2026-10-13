
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone




class ProfileTheme(models.Model):
    """Các theme có thể mở khóa cho trang cá nhân."""

    slug = models.SlugField(
        max_length=50,
        unique=True,
        verbose_name="Mã theme",
    )
    name = models.CharField(
        max_length=100,
        verbose_name="Tên theme",
    )
    description = models.CharField(
        max_length=250,
        blank=True,
        verbose_name="Mô tả",
    )
    xp_cost = models.PositiveIntegerField(
        default=0,
        verbose_name="XP cần thiết",
    )
    required_likes = models.PositiveIntegerField(
        default=0,
        verbose_name="Số lượt thích yêu cầu",
    )
    background_key = models.CharField(
        max_length=30,
        choices=[
            ("cyber_blue", "Cyber Blue"),
            ("pixel_forest", "Pixel Forest"),
            ("void_realm", "Void Realm"),
            ("crimson_eclipse", "Crimson Eclipse"),
            ("neon_abyss", "Neon Abyss"),
            ("solar_flare", "Solar Flare"),
        ],
        default="cyber_blue",
        verbose_name="Kiểu background",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Đang kinh doanh",
    )

    class Meta:
        ordering = ["xp_cost", "name"]
        verbose_name = "Theme cá nhân"
        verbose_name_plural = "Theme cá nhân"

    def __str__(self):
        return self.name


class MemberProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="member_profile",
    )
    avatar = models.ImageField(
        upload_to="avatars/",
        blank=True,
        null=True,
        verbose_name="Ảnh đại diện",
    )
    bio = models.CharField(
        max_length=250,
        blank=True,
        verbose_name="Giới thiệu bản thân",
    )

    INTEREST_CHOICES = [
        ("web", "Web Development"),
        ("ai", "AI & Data"),
        ("game", "Game Development"),
        ("mobile", "Mobile Development"),
        ("security", "Cybersecurity"),
        ("other", "Khác"),
    ]

    interests = models.CharField(
        max_length=20,
        choices=INTEREST_CHOICES,
        blank=True,
        verbose_name="Lĩnh vực quan tâm",
    )
    skills = models.CharField(
        max_length=250,
        blank=True,
        verbose_name="Kỹ năng",
        help_text="Ví dụ: Python, Django, C#, Unity",
    )
    github_url = models.URLField(
        max_length=200,
        blank=True,
        verbose_name="GitHub",
    )
    portfolio_url = models.URLField(
        max_length=200,
        blank=True,
        verbose_name="Portfolio",
    )

    # Developer Space
    xp = models.PositiveIntegerField(
        default=0,
        verbose_name="Kinh nghiệm",
    )
    unlocked_themes = models.ManyToManyField(
        ProfileTheme,
        blank=True,
        related_name="unlocked_by_members",
        verbose_name="Theme đã mở khóa",
    )
    active_theme = models.ForeignKey(
        ProfileTheme,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="active_profiles",
        verbose_name="Theme đang sử dụng",
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Cập nhật lần cuối",
    )

    def __str__(self):
        return f"Hồ sơ của {self.user.username}"


class XPTransaction(models.Model):
    """Lịch sử cộng XP để kiểm tra và chống nhận thưởng trùng."""

    profile = models.ForeignKey(
        MemberProfile,
        on_delete=models.CASCADE,
        related_name="xp_transactions",
    )
    amount = models.PositiveIntegerField(
        verbose_name="XP nhận được",
    )
    reason = models.CharField(
        max_length=200,
        verbose_name="Lý do",
    )
    event_key = models.CharField(
        max_length=100,
        verbose_name="Mã sự kiện",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["profile", "event_key"],
                name="unique_profile_xp_event",
            )
        ]

    def __str__(self):
        return f"{self.profile.user.username}: +{self.amount} XP"


class Achievement(models.Model):
    """Danh mục thành tích của cộng đồng."""

    slug = models.SlugField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=250, blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Thành tích"
        verbose_name_plural = "Thành tích"

    def __str__(self):
        return self.name


class MemberAchievement(models.Model):
    """Thành tích mà một thành viên đã đạt."""

    profile = models.ForeignKey(
        MemberProfile,
        on_delete=models.CASCADE,
        related_name="achievements",
    )
    achievement = models.ForeignKey(
        Achievement,
        on_delete=models.CASCADE,
        related_name="members",
    )
    earned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["profile", "achievement"],
                name="unique_member_achievement",
            )
        ]
        ordering = ["-earned_at"]

    def __str__(self):
        return (
            f"{self.profile.user.username} - "
            f"{self.achievement.name}"
        )



class MemberPost(models.Model):
    STATUS_CHOICES = [
        ("draft", "Bản nháp"),
        ("published", "Đã đăng"),
    ]

    author = models.ForeignKey(
        "auth.User",
        on_delete=models.CASCADE,
        related_name="member_posts",
    )

    title = models.CharField(
        "Tiêu đề",
        max_length=200,
    )

    description = models.TextField(
        "Giới thiệu",
    )

    thumbnail = models.ImageField(
        "Ảnh đại diện bài viết",
        upload_to="member_posts/thumbnails/",
    )

    content_images = models.JSONField(
        "Danh sách hình ảnh",
        default=list,
        blank=True,
    )

    
    video_url = models.URLField(
        "Video YouTube",
        max_length=500,
        blank=True,
    )


    github_url = models.URLField(
        "Link GitHub",
        blank=True,
    )

    demo_url = models.URLField(
        "Link demo",
        blank=True,
    )

    status = models.CharField(
        "Trạng thái",
        max_length=20,
        choices=STATUS_CHOICES,
        default="draft",
    )

    created_at = models.DateTimeField(
        "Ngày tạo",
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        "Ngày cập nhật",
        auto_now=True,
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Bài viết thành viên"
        verbose_name_plural = "Bài viết thành viên"

    def __str__(self):
        return f"{self.title} - {self.author.username}"


class Announcement(models.Model):
    PRIORITY_CHOICES = [
        ("normal", "Thông thường"),
        ("important", "Quan trọng"),
        ("urgent", "Khẩn cấp"),
    ]

    title = models.CharField(
        "Tiêu đề",
        max_length=200,
    )
    summary = models.CharField(
        "Mô tả ngắn",
        max_length=300,
        blank=True,
    )
    content = models.TextField("Nội dung")
    is_deleted = models.BooleanField(
    "Đã xóa",
    default=False,
    )

    priority = models.CharField(
        "Mức độ",
        max_length=20,
        choices=PRIORITY_CHOICES,
        default="normal",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="club_announcements",
        verbose_name="Người đăng",
    )
    is_published = models.BooleanField(
        "Công khai",
        default=True,
    )
    published_at = models.DateTimeField(
        "Ngày đăng",
        default=timezone.now,
    )
    created_at = models.DateTimeField(
        "Ngày tạo",
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        "Ngày cập nhật",
        auto_now=True,
    )

    class Meta:
        ordering = ["-published_at", "-created_at"]
        verbose_name = "Thông báo"
        verbose_name_plural = "Thông báo"

    def __str__(self):
        return self.title

    image = models.ImageField(
    "Ảnh đính kèm",
    upload_to="announcements/images/",
    blank=True,
    null=True,
    )

    video = models.FileField(
        "Video đính kèm",
        upload_to="announcements/videos/",
        blank=True,
        null=True,
    )


# ============================================================
# FORUM - DIỄN ĐÀN THẢO LUẬN IT MUCE
# ============================================================

class ForumTopic(models.Model):
    """Chủ đề thảo luận của thành viên."""

    STATUS_CHOICES = [
        ("pending", "Chờ duyệt"),
        ("published", "Đã đăng"),
        ("hidden", "Đã ẩn"),
        ("rejected", "Từ chối"),
    ]

    CATEGORY_CHOICES = [
        ("question", "Hỏi đáp"),
        ("sharing", "Chia sẻ kiến thức"),
        ("discussion", "Thảo luận"),
        ("project", "Dự án"),
        ("career", "Học tập và nghề nghiệp"),
        ("other", "Khác"),
    ]

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="forum_topics",
        verbose_name="Người đăng",
    )
    title = models.CharField(
        "Tiêu đề",
        max_length=200,
    )
    content = models.TextField("Nội dung")
    category = models.CharField(
        "Danh mục",
        max_length=20,
        choices=CATEGORY_CHOICES,
        default="discussion",
    )

    video_url = models.URLField(
    max_length=500,
    blank=True,
    default="",
    )
    
    status = models.CharField(
        "Trạng thái",
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
        db_index=True,
    )
    published_at = models.DateTimeField(
        "Ngày đăng công khai",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(
        "Ngày tạo",
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        "Ngày cập nhật",
        auto_now=True,
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Chủ đề diễn đàn"
        verbose_name_plural = "Chủ đề diễn đàn"

    def __str__(self):
        return self.title

    @property
    def like_count(self):
        return self.likes.count()

    @property
    def comment_count(self):
        return self.comments.filter(status="published").count()


class ForumTopicImage(models.Model):
    """Ảnh đính kèm của một chủ đề Forum."""

    topic = models.ForeignKey(
        ForumTopic,
        on_delete=models.CASCADE,
        related_name="images",
        verbose_name="Chủ đề",
    )

    image = models.ImageField(
        upload_to="forum/topics/%Y/%m/",
        verbose_name="Ảnh đính kèm",
    )

    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Ngày tải lên",
    )

    class Meta:
        ordering = ["uploaded_at"]
        verbose_name = "Ảnh chủ đề Forum"
        verbose_name_plural = "Ảnh chủ đề Forum"

    def __str__(self):
        return f"Ảnh của chủ đề: {self.topic.title}"



class ForumComment(models.Model):
    """Bình luận trong một chủ đề."""

    STATUS_CHOICES = [
        ("published", "Đã đăng"),
        ("hidden", "Đã ẩn"),
        ("pending", "Chờ duyệt"),
    ]

    topic = models.ForeignKey(
        ForumTopic,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name="Chủ đề",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="forum_comments",
        verbose_name="Người bình luận",
    )

    content = models.TextField("Nội dung")
    is_deleted = models.BooleanField("Đã xóa", default=False)
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="replies",
        verbose_name="Bình luận được trả lời",
    )
        

    status = models.CharField(
        "Trạng thái",
        max_length=20,
        choices=STATUS_CHOICES,
        default="published",
        db_index=True,
    )
    created_at = models.DateTimeField(
        "Ngày tạo",
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        "Ngày cập nhật",
        auto_now=True,
    )

    class Meta:
        ordering = ["created_at"]
        verbose_name = "Bình luận diễn đàn"
        verbose_name_plural = "Bình luận diễn đàn"

    def __str__(self):
        return f"Bình luận của {self.author.username}"


class ForumLike(models.Model):
    """Một thành viên chỉ có một lượt Like cho mỗi chủ đề."""

    topic = models.ForeignKey(
        ForumTopic,
        on_delete=models.CASCADE,
        related_name="likes",
        verbose_name="Chủ đề",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="forum_likes",
        verbose_name="Người thích",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["topic", "user"],
                name="unique_forum_like",
            ),
        ]
        verbose_name = "Lượt thích diễn đàn"
        verbose_name_plural = "Lượt thích diễn đàn"

    def __str__(self):
        return f"{self.user.username} thích {self.topic.title}"


class ForumReport(models.Model):
    """Báo cáo chủ đề hoặc bình luận vi phạm."""

    REASON_CHOICES = [
        ("spam", "Spam hoặc quảng cáo"),
        ("harassment", "Công kích hoặc quấy rối"),
        ("misinformation", "Thông tin sai lệch"),
        ("inappropriate", "Nội dung không phù hợp"),
        ("malicious_link", "Liên kết đáng ngờ"),
        ("other", "Lý do khác"),
    ]

    STATUS_CHOICES = [
        ("pending", "Chờ xử lý"),
        ("resolved", "Đã xử lý"),
        ("dismissed", "Không vi phạm"),
    ]

    reporter = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="forum_reports",
        verbose_name="Người báo cáo",
    )
    topic = models.ForeignKey(
        ForumTopic,
        on_delete=models.CASCADE,
        related_name="reports",
        verbose_name="Chủ đề liên quan",
    )
    comment = models.ForeignKey(
        ForumComment,
        on_delete=models.CASCADE,
        related_name="reports",
        null=True,
        blank=True,
        verbose_name="Bình luận liên quan",
    )
    reason = models.CharField(
        "Lý do",
        max_length=30,
        choices=REASON_CHOICES,
    )
    details = models.CharField(
        "Mô tả bổ sung",
        max_length=500,
        blank=True,
    )
    status = models.CharField(
        "Trạng thái xử lý",
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
    )
    resolved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resolved_forum_reports",
    )

    class Meta:
        ordering = ["status", "-created_at"]
        verbose_name = "Báo cáo diễn đàn"
        verbose_name_plural = "Báo cáo diễn đàn"

    def __str__(self):
        return f"Báo cáo #{self.pk} - {self.get_reason_display()}"


class ForumModerationLog(models.Model):
    """Lịch sử kiểm duyệt để truy vết hành động của quản trị viên."""

    ACTION_CHOICES = [
        ("approve", "Duyệt"),
        ("hide", "Ẩn"),
        ("reject", "Từ chối"),
        ("restore", "Khôi phục"),
        ("warn", "Cảnh cáo"),
        ("restrict", "Hạn chế thành viên"),
    ]

    moderator = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="forum_moderation_actions",
        verbose_name="Người kiểm duyệt",
    )
    topic = models.ForeignKey(
        ForumTopic,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="moderation_logs",
    )
    comment = models.ForeignKey(
        ForumComment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="moderation_logs",
    )
    action = models.CharField(
        "Hành động",
        max_length=20,
        choices=ACTION_CHOICES,
    )
    note = models.CharField(
        "Ghi chú",
        max_length=500,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Lịch sử kiểm duyệt"
        verbose_name_plural = "Lịch sử kiểm duyệt"

    def __str__(self):
        return f"{self.get_action_display()} - #{self.pk}"
