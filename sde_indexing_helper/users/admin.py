from django.contrib import admin
from django.contrib.auth import admin as auth_admin
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from sde_indexing_helper.users.forms import UserAdminChangeForm, UserAdminCreationForm
from sde_indexing_helper.users.models import (
    ContactFormModel,
    ContentCurationRequestModel,
)

User = get_user_model()


@admin.register(User)
class UserAdmin(auth_admin.UserAdmin):
    form = UserAdminChangeForm
    add_form = UserAdminCreationForm
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (_("Personal info"), {"fields": ("name", "email")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    list_display = ["username", "name", "is_superuser"]
    search_fields = ["name"]


@admin.register(ContactFormModel)
class ContactFormAdmin(admin.ModelAdmin):
    list_display = ["name", "email", "subject", "comment"]
    search_fields = ["name", "email"]
    list_filter = ["subject"]


@admin.register(ContentCurationRequestModel)
class ContentCurationRequestAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "email",
        "scientific_focus",
        "data_type",
        "data_link",
        "additional_info",
    ]
    search_fields = ["name", "scientific_focus", "data_type"]
    list_filter = ["scientific_focus", "data_type"]
