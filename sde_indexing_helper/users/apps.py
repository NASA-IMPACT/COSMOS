from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class UsersConfig(AppConfig):
    name = "sde_indexing_helper.users"
    verbose_name = _("Users")

    def ready(self):
        try:
            import sde_indexing_helper.users.signals  # noqa F401
        except ImportError:
            pass
