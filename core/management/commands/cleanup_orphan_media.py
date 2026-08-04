import os
import posixpath

from django.conf import settings
from django.core.management.base import BaseCommand

from category.models import Category
from company.models import Company
from store.models import Product, ProductGallery
from accounts.models import UserProfile


def _relpath(full_path, media_root):
    rel = os.path.relpath(full_path, media_root)
    return rel.replace(os.sep, '/')


class Command(BaseCommand):
    help = 'Find and delete orphaned media files not referenced by any model.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            dest='dry_run',
            default=False,
            help='List orphan files without deleting them.',
        )

    def handle(self, *args, **options):
        media_root = settings.MEDIA_ROOT

        referenced = set()

        for p in Product.objects.values_list('images', flat=True):
            if p:
                referenced.add(str(p))

        for g in ProductGallery.objects.values_list('image', flat=True):
            if g:
                referenced.add(str(g))

        for c in Category.objects.values_list('cat_image', flat=True):
            if c:
                referenced.add(str(c))

        for c in Company.objects.values_list('logo', flat=True):
            if c:
                referenced.add(str(c))

        for c in Company.objects.values_list('cover_image', flat=True):
            if c:
                referenced.add(str(c))

        for u in UserProfile.objects.values_list('profile_picture', flat=True):
            if u:
                referenced.add(str(u))

        self.stdout.write(f'Referenced files in DB: {len(referenced)}')

        disk_files = set()
        for dirpath, dirnames, filenames in os.walk(media_root):
            for filename in filenames:
                full_path = os.path.join(dirpath, filename)
                rel_path = _relpath(full_path, media_root)
                disk_files.add(rel_path)

        self.stdout.write(f'Files on disk: {len(disk_files)}')

        orphans = disk_files - referenced
        self.stdout.write(f'Orphan files: {len(orphans)}')

        if not orphans:
            self.stdout.write(self.style.SUCCESS('No orphan files found.'))
            return

        if options.get('dry_run'):
            self.stdout.write('Dry run mode. No files deleted.')
            for orphan in sorted(orphans):
                self.stdout.write(f'  {orphan}')
            return

        deleted = 0
        for orphan in sorted(orphans):
            full_path = os.path.join(media_root, orphan.replace('/', os.sep))
            try:
                os.remove(full_path)
                deleted += 1
                self.stdout.write(f'Deleted: {orphan}')
            except OSError as e:
                self.stderr.write(f'Error deleting {orphan}: {e}')

        self.stdout.write(self.style.SUCCESS(f'Deleted {deleted} orphan file(s).'))