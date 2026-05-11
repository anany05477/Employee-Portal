from django.core.management.base import BaseCommand
from django.conf import settings
from pathlib import Path
import shutil
from datetime import datetime


class Command(BaseCommand):
    help = 'Create a timestamped backup of the SQLite database.'

    def handle(self, *args, **options):
        db_path = Path(settings.DATABASES['default']['NAME'])
        backup_root = Path(settings.BACKUP_ROOT)
        backup_root.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = backup_root / f'db_backup_{timestamp}.sqlite3'

        if not db_path.exists():
            self.stdout.write(self.style.ERROR(f'Database file not found: {db_path}'))
            return

        shutil.copy2(db_path, backup_file)
        self.stdout.write(self.style.SUCCESS(f'Database backup created at {backup_file}'))
