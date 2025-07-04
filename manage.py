#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'test_portal.settings')

    # ✅ Auto-create superuser in production if CREATE_SUPERUSER=1
    if os.environ.get('CREATE_SUPERUSER') == '1':
        import django
        django.setup()
        from django.contrib.auth import get_user_model
        User = get_user_model()

        username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'petrox')
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'petrox@gmail.com')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'petroxAdmin')

        if not User.objects.filter(username=username).exists():
            print(f"🛠 Creating superuser '{username}'...")
            User.objects.create_superuser(username, email, password)
        else:
            print(f"✔ Superuser '{username}' already exists.")

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()
