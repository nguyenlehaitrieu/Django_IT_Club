
from django import forms
from django.contrib.auth.models import User
from .models import MemberProfile, MemberPost
from .models import Announcement



class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]

        labels = {
            "first_name": "Tên",
            "last_name": "Họ và tên đệm",
            "email": "Email",
        }

        widgets = {
            "first_name": forms.TextInput(attrs={
                "placeholder": "Nhập tên",
                "autocomplete": "given-name",
            }),
            "last_name": forms.TextInput(attrs={
                "placeholder": "Nhập họ và tên đệm",
                "autocomplete": "family-name",
            }),
            "email": forms.EmailInput(attrs={
                "placeholder": "you@example.com",
                "autocomplete": "email",
            }),
        }


class MemberProfileForm(forms.ModelForm):
    class Meta:
        model = MemberProfile
        fields = [
            "avatar",
            "bio",
            "interests",
            "skills",
            "github_url",
            "portfolio_url",
        ]

        labels = {
            "avatar": "Ảnh đại diện",
            "bio": "Giới thiệu bản thân",
            "interests": "Lĩnh vực quan tâm",
            "skills": "Kỹ năng",
            "github_url": "GitHub",
            "portfolio_url": "Portfolio cá nhân",
        }

        widgets = {
            "avatar": forms.ClearableFileInput(attrs={
                "accept": "image/jpeg,image/png,image/webp,image/gif",
                "class": "profile-avatar-input",
            }),
            "bio": forms.Textarea(attrs={
                "placeholder": "Chia sẻ đôi điều về bạn...",
                "rows": 3,
                "maxlength": 250,
            }),
            "interests": forms.Select(attrs={
                "class": "profile-select",
            }),
            "skills": forms.TextInput(attrs={
                "placeholder": "Python, Django, C#, Unity...",
            }),
            "github_url": forms.URLInput(attrs={
                "placeholder": "https://github.com/username",
            }),
            "portfolio_url": forms.URLInput(attrs={
                "placeholder": "https://your-portfolio.com",
            }),
        }


class MemberPostForm(forms.ModelForm):
    class Meta:
        model = MemberPost
        fields = [
            "title",
            "description",
            "thumbnail",
            "video_url",
            "github_url",
            "demo_url",
        ]

        labels = {
            "title": "Tiêu đề bài viết",
            "description": "Giới thiệu",
            "thumbnail": "Ảnh thumbnail",
            "content_images": "Danh sách hình ảnh",
            "video_url": "Link video demo",
            "github_url": "Link GitHub",
            "demo_url": "Link demo",
        }

        widgets = {
            "title": forms.TextInput(attrs={
                "placeholder": "Ví dụ: MiniJudge Classroom",
            }),
            "description": forms.Textarea(attrs={
                "rows": 5,
                "placeholder": "Giới thiệu dự án, chức năng và công nghệ sử dụng...",
            }),
            "video_url": forms.URLInput(attrs={
                "placeholder": "https://youtube.com/...",
            }),
            "github_url": forms.URLInput(attrs={
                "placeholder": "https://github.com/username/project",
            }),
            "demo_url": forms.URLInput(attrs={
                "placeholder": "https://...",
            }),
        }





from django import forms
from .models import Announcement


class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = [
            "title",
            "summary",
            "content",
            "priority",
            "image",
            "video",
            "is_published",
        ]

        labels = {
            "title": "Tiêu đề thông báo",
            "summary": "Mô tả ngắn",
            "content": "Nội dung chi tiết",
            "priority": "Mức độ ưu tiên",
            "image": "Ảnh đính kèm",
            "video": "Video đính kèm",
            "is_published": "Công khai thông báo",
        }

        widgets = {
            "title": forms.TextInput(
                attrs={"placeholder": "Nhập tiêu đề thông báo..."}
            ),
            "summary": forms.TextInput(
                attrs={"placeholder": "Tóm tắt nội dung trong một câu..."}
            ),
            "content": forms.Textarea(
                attrs={
                    "rows": 12,
                    "placeholder": "Nhập nội dung thông báo...",
                }
            ),
            "priority": forms.Select(),
            "image": forms.ClearableFileInput(
                attrs={"accept": "image/*"}
            ),
            "video": forms.ClearableFileInput(
                attrs={"accept": "video/mp4,video/webm,video/ogg"}
            ),
            "is_published": forms.CheckboxInput(),
        }

    def clean_image(self):
        image = self.cleaned_data.get("image")

        if image and image.size > 10 * 1024 * 1024:
            raise forms.ValidationError(
                "Ảnh không được vượt quá 10 MB."
            )

        return image

    def clean_video(self):
        video = self.cleaned_data.get("video")

        if video:
            allowed_types = {
                "video/mp4",
                "video/webm",
                "video/ogg",
            }

            if video.content_type not in allowed_types:
                raise forms.ValidationError(
                    "Chỉ chấp nhận video MP4, WebM hoặc OGG."
                )

            if video.size > 100 * 1024 * 1024:
                raise forms.ValidationError(
                    "Video không được vượt quá 100 MB."
                )

        return video

