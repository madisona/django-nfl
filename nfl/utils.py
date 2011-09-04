
from django.core.cache import cache

# A similar feature might make it into a future version of django,
# but for now we'll just use it here.
# https://code.djangoproject.com/attachment/ticket/12982/
def get_or_add_qs(key, qs, **kwargs):
    """
    Fetch a given key from the cache. If the key does not exist,
    evaluate the queryset and store the results in cache.
    """
    val = cache.get(key)
    if val is None:
        val = list(qs) # force qs to be evaluated
        cache.add(key, val, **kwargs)
    return val