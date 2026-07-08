import logging

import requests
from django.core.cache import cache

logger = logging.getLogger(__name__)

# Fallback rate used only if the live rate service is unreachable.
# 1 LKR is worth roughly this many USD. Update as needed.
FALLBACK_LKR_TO_USD = 0.0033
RATE_CACHE_KEY = "lkr_to_usd_rate"
RATE_CACHE_TTL = 60 * 60  # 1 hour


def get_lkr_to_usd_rate():
    """Return the live LKR -> USD exchange rate, cached for one hour.

    Falls back to a hardcoded rate if the rate service is unavailable so the
    checkout flow never breaks.
    """
    cached = cache.get(RATE_CACHE_KEY)
    if cached is not None:
        return cached
    try:
        resp = requests.get("https://open.er-api.com/v6/latest/LKR", timeout=5)
        resp.raise_for_status()
        data = resp.json()
        rate = float(data["rates"]["USD"])
        cache.set(RATE_CACHE_KEY, rate, RATE_CACHE_TTL)
        return rate
    except (requests.RequestException, KeyError, ValueError, TypeError) as e:
        logger.warning("Failed to fetch live LKR->USD rate, using fallback: %s", e)
        return FALLBACK_LKR_TO_USD


def convert_lkr_to_usd(amount_lkr, rate=None):
    if rate is None:
        rate = get_lkr_to_usd_rate()
    return round(float(amount_lkr) * rate, 2)
