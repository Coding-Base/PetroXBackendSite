"""
send_emailmessage management command removed.

The bulk email management command was part of the removed EmailMessage feature. This stub
keeps the command file present so deployments that reference it don't fail, but it will
raise an informative error if executed.
"""

from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
    help = "(Removed) send_emailmessage command. EmailMessage feature was removed from the project."

    def handle(self, *args, **options):
        raise CommandError('send_emailmessage command removed: EmailMessage feature disabled in this project')
