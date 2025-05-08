from django.apps import AppConfig


class MoiraflowConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'moiraflow'

    def ready(self):
        """
        Se ejecuta cuando la aplicación está lista
        """
        from moiraflow import signals
        signals.conectar_signals()