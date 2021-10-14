from django.apps import AppConfig


class InventoryConfig(AppConfig):
    name = 'supplyr.inventory'

    def ready(self):
        import supplyr.inventory.signals