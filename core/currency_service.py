import requests
from decimal import Decimal
from django.conf import settings
from django.core.cache import cache


class CurrencyConverter:
    """
    Service for converting currencies using ExchangeRate-API
    """
    BASE_URL = "https://v6.exchangerate-api.com/v6"
    CACHE_TIMEOUT = 3600  # Cache for 1 hour

    @classmethod
    def get_exchange_rate(cls, from_currency='EUR', to_currency='USD'):
        """
        Get exchange rate from one currency to another
        Uses caching to reduce API calls
        """
        cache_key = f'exchange_rate_{from_currency}_{to_currency}'

        # Try to get from cache first
        cached_rate = cache.get(cache_key)
        if cached_rate:
            return Decimal(str(cached_rate))

        try:
            api_key = settings.EXCHANGE_RATE_API_KEY
            url = f"{cls.BASE_URL}/{api_key}/pair/{from_currency}/{to_currency}"

            response = requests.get(url, timeout=5)
            response.raise_for_status()

            data = response.json()

            if data.get('result') == 'success':
                rate = Decimal(str(data['conversion_rate']))
                # Cache the rate
                cache.set(cache_key, float(rate), cls.CACHE_TIMEOUT)
                return rate
            else:
                # Fallback to hardcoded rate if API fails
                return cls._get_fallback_rate(from_currency, to_currency)

        except (requests.RequestException, KeyError, ValueError):
            # Fallback to hardcoded rate on error
            return cls._get_fallback_rate(from_currency, to_currency)

    @staticmethod
    def _get_fallback_rate(from_currency, to_currency):
        """Fallback exchange rates if API is unavailable"""
        fallback_rates = {
            ('EUR', 'USD'): Decimal('1.10'),
            ('USD', 'EUR'): Decimal('0.91'),
            ('EUR', 'EUR'): Decimal('1.00'),
            ('USD', 'USD'): Decimal('1.00'),
        }
        return fallback_rates.get((from_currency, to_currency), Decimal('1.00'))

    @classmethod
    def convert(cls, amount, from_currency='EUR', to_currency='USD'):
        """
        Convert amount from one currency to another
        """
        if from_currency == to_currency:
            return Decimal(str(amount))

        rate = cls.get_exchange_rate(from_currency, to_currency)
        return Decimal(str(amount)) * rate
