#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))


def main():
    """Run administrative tasks."""
    
    # IMPORTANT: this must match your project folder name
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Make sure Django is installed "
            "and available in your environment."
        ) from exc

    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()