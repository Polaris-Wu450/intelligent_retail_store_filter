from django.core.management.base import BaseCommand
from retailops.models import Store


class Command(BaseCommand):
    help = 'Seed sample store data for development'

    def handle(self, *args, **options):
        stores_data = [
            {'store_id': 'S001', 'name': 'Downtown Flagship Store'},
            {'store_id': 'S002', 'name': 'Westside Mall Branch'},
            {'store_id': 'S003', 'name': 'Airport Plaza Outlet'},
            {'store_id': 'S004', 'name': 'Riverside Shopping Center'},
            {'store_id': 'S005', 'name': 'North District Store'},
        ]

        created_count = 0
        for store_data in stores_data:
            store, created = Store.objects.get_or_create(
                store_id=store_data['store_id'],
                defaults={'name': store_data['name']}
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f"✓ Created: {store.name} ({store.store_id})")
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f"⚠ Already exists: {store.name} ({store.store_id})")
                )

        self.stdout.write(
            self.style.SUCCESS(f"\n✅ Seed completed: {created_count} new stores created")
        )
