from django.apps import AppConfig


class InferenceConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "inference"
    verbose_name = "Inference"

    def ready(self):
        import inference.signals  # noqa F401
