import os

from app.workers.celery_app import celery  # noqa: F401
from app.workers import tasks  # noqa: F401


def main() -> None:
    # Standard Celery worker entrypoint. Command is handled by container/CLI.
    print("IntelliFlow Celery worker starting...")
    # This file exists mainly for local readability.
    _ = os.environ.get("CELERY_WORKER_CONCURRENCY", "1")


if __name__ == "__main__":
    main()

