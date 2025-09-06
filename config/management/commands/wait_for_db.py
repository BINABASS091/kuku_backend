import time
from django.core.management.base import BaseCommand
from django.db import connections
from django.db.utils import OperationalError

class Command(BaseCommand):
    """Django command to wait for database to be available"""
    
    def handle(self, *args, **options):
        self.stdout.write('Waiting for database...')
        db_conn = None
        max_retries = 30  # 30 * 2 seconds = 1 minute max wait
        retry_count = 0
        
        while not db_conn:
            try:
                # Try to connect to the database
                connections['default'].ensure_connection()
                db_conn = True
                self.stdout.write(self.style.SUCCESS('Database is available!'))
            except OperationalError:
                retry_count += 1
                if retry_count >= max_retries:
                    self.stdout.write(
                        self.style.ERROR('Max retries reached. Database is not available.')
                    )
                    raise
                
                self.stdout.write('Database unavailable, waiting 2 seconds...')
                time.sleep(2)
