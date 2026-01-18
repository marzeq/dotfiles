from typing import Callable, Literal

import util
import shlex
import re
import aiohttp
import asyncio
import time
from typing import Any

from .base_mode import LauncherMode, LauncherResult
from .currencies import lookup_currency
from .settings import launcher_settings

API_BASE = "https://open.er-api.com/v6/latest"


class CurrencyMode(LauncherMode):
    async def get_results(self, launcher, query, emit):
        q = query.strip()
        if not q:
            return

        ok, amount, source, target = parse_currency_query(q)
        if not ok or amount is None or source is None:
            return

        calculated = await calculate(amount, source, target)
        if calculated is None:
            return

        calculated = round(calculated, 2)
        result_text = f"{calculated} {target or launcher_settings.preferred_currency}"

        emit(
            [
                LauncherCurrencyResult(
                    result_text,
                    lambda: self.launch(launcher),
                )
            ],
            False,
        )

    def launch(self, launcher):
        result = launcher.get_results()[0]
        if isinstance(result, LauncherCurrencyResult) and result.result is not None:
            launcher.set_entry_text(f"{result.result}")
            if util.has_command("wl-copy"):
                util.shell(f"wl-copy {shlex.quote(result.result)}")


class LauncherCurrencyResult(LauncherResult):
    def __init__(self, result: str, launch: Callable[[], None]):
        super().__init__(
            value=result,
            icon_name="accessories-calculator-symbolic",
            launch=launch,
            css_classes=["launcher-result-value"],
        )
        self.result = result


ParseResult = (
    tuple[Literal[True], float, str, str | None]
    | tuple[Literal[False], None, None, None]
)


def parse_currency_query(query: str) -> ParseResult:
    q = query.strip()

    # (amount) (CURRENCY)
    m = re.fullmatch(r"(\d+(?:\.\d+)?)\s*(\S+)", q)
    if m:
        source = lookup_currency(m.group(2))
        if source is not None:
            return True, float(m.group(1)), source, None

    # (amount) (CURRENCY) to|in (CURRENCY)
    m = re.fullmatch(
        r"(\d+(?:\.\d+)?)\s*(\S+)\s+(?:to|in)\s+(\S+)",
        q,
    )
    if m:
        source = lookup_currency(m.group(2))
        target = lookup_currency(m.group(3))
        if source is not None and target is not None:
            return True, float(m.group(1)), source, target

    # (CURRENCY)
    m = re.fullmatch(r"(\S+)", q)
    if m:
        source = lookup_currency(m.group(1))
        if source is not None:
            return True, 1.0, source, None

    # (CURRENCY) to|in (CURRENCY)
    m = re.fullmatch(r"(\S+)\s+(?:to|in)\s+(\S+)", q)
    if m:
        source = lookup_currency(m.group(1))
        target = lookup_currency(m.group(2))
        if source is not None and target is not None:
            return True, 1.0, source, target

    return False, None, None, None


_rate_cache: dict[str, dict[str, Any]] = {}
_cache_lock = asyncio.Lock()


async def _get_rates(base: str) -> dict[str, float] | None:
    base = base.upper()
    now = time.time()

    async with _cache_lock:
        cached = _rate_cache.get(base)
        if cached and cached["expires_at"] > now:
            return cached["rates"]

    url = f"{API_BASE}/{base}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
    except (aiohttp.ClientError, asyncio.TimeoutError):
        return None

    if data.get("result") != "success":
        return None

    rates = data.get("rates")
    if not isinstance(rates, dict):
        return None

    expires_at = data.get("time_next_update_unix")
    if not isinstance(expires_at, (int, float)):
        expires_at = now + 86400

    async with _cache_lock:
        _rate_cache[base] = {
            "rates": rates,
            "expires_at": expires_at,
        }

    return rates


async def calculate(amount: float, source: str, target: str | None) -> float | None:
    if target is None:
        target = launcher_settings.preferred_currency

    rates = await _get_rates(source)
    if rates is None:
        return None

    rate = rates.get(target.upper())
    if rate is None:
        return None

    return amount * rate
