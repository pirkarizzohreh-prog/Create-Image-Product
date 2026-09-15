def absolutize(context, url):
    """Turn a (possibly relative, e.g. local FileSystemStorage) URL into an
    absolute one using the current request, so the frontend (served from a
    different origin/port) can load it directly. S3/R2-backed storage
    already returns absolute signed URLs, so this is a no-op there."""
    if not url:
        return url
    request = context.get("request") if context else None
    if request is not None:
        return request.build_absolute_uri(url)
    return url
