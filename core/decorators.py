
from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def role_required(*allowed_roles):
    """
    Chỉ cho phép người dùng thuộc một trong các nhóm được chỉ định.
    Superuser được phép truy cập.
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            user = request.user

            if user.is_superuser:
                return view_func(request, *args, **kwargs)

            if user.groups.filter(
                name__in=allowed_roles
            ).exists():
                return view_func(request, *args, **kwargs)

            raise PermissionDenied(
                "Bạn không có quyền truy cập chức năng này."
            )

        return wrapper

    return decorator
