import logging

from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def notify_uploader(job, subject, message):
    """Best-effort notification to the image's uploader. Uses Django's email
    backend (console backend in dev by default via settings) so this works
    out of the box without extra infra, and is easy to swap for a real
    transactional email provider in prod."""
    user = job.image.uploaded_by
    if not user or not user.email:
        return
    try:
        send_mail(subject, message, None, [user.email], fail_silently=True)
    except Exception:
        logger.exception("Failed to send review notification for job %s", job.id)
