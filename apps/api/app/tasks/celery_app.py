from __future__ import annotations

from app.core.config import settings

try:
    from celery import Celery
except ImportError:  # pragma: no cover
    Celery = None


if Celery is not None:
    celery_app = Celery(
        "biomarkly",
        broker=settings.celery_broker_url,
        backend=settings.celery_result_backend,
        include=["app.tasks.jobs"],
    )
    celery_app.conf.update(task_serializer="json", result_serializer="json", accept_content=["json"])
else:
    class _Result:
        def __init__(self, value: str) -> None:
            self.id = value


    class _TaskWrapper:
        def __init__(self, fn):
            self.fn = fn

        def __call__(self, *args, **kwargs):
            return self.fn(*args, **kwargs)

        def delay(self, *args, **kwargs):
            return _Result(self.fn(*args, **kwargs))


    class _CeleryShim:
        def task(self, name: str):
            def decorator(fn):
                return _TaskWrapper(fn)

            return decorator


    celery_app = _CeleryShim()
