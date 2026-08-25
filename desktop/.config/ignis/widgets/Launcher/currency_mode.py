from typing import Literal

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
    def build(self, launcher):
        super().build(launcher)
        self.set_results([LauncherCurrencyResult("", lambda: self.launch())])
        self.results[0].visible = False
        self.section.visible = False
        return self.section

    async def update(self, query: str, refresh):
        result_widget = self.results[0]
        q = query.strip()
        if not q:
            result_widget.visible = False
            self.section.visible = False
            refresh()
            return

        ok, amount, source, target = parse_currency_query(q)
        if not ok or amount is None or source is None:
            result_widget.visible = False
            self.section.visible = False
            refresh()
            return

        calculated = await calculate(amount, source, target)
        if calculated is None:
            result_widget.visible = False
            self.section.visible = False
            refresh()
            return

        calculated = round(calculated, 2)
        result_text = f"{calculated} {target or launcher_settings.preferred_currency}"

        result_widget.set_value(result_text)
        result_widget.amount = calculated
        result_widget.target = target or launcher_settings.preferred_currency
        result_widget.visible = True
        self.section.visible = True
        refresh()

    def launch(self):
        if not self.results:
            return

        result = self.results[0]
        if isinstance(result, LauncherCurrencyResult) and hasattr(result, 'amount') and hasattr(result, 'target'):
            entry_text = f"{result.amount} {result.target}"
            if self.launcher is not None:
                self.launcher.set_entry_text(entry_text)


class LauncherCurrencyResult(LauncherResult):
    def __init__(self, result: str, launch):
        super().__init__(
            value=result,
            icon_name="accessories-calculator-symbolic",
            launch=launch,
            css_classes=["launcher-result-value"],
        )
        self.result = result
        self.amount: float = 0.0
        self.target: str = ""


ParseResult = (
    tuple[Literal[True], float, str, str | None]
    | tuple[Literal[False], None, None, None]
)


_NUMBER_RE = r"\d+(?:[\, _]\d+)*(?:\.\d+(?:[\, _]\d+)*)?"


def parse_number(s: str) -> float:
    return float(s.replace(" ", "").replace("_", "").replace(",", ""))


def parse_currency_query(query: str) -> ParseResult:
    q = query.strip()

    # (amount) (CURRENCY) to|in (CURRENCY)?
    m = re.fullmatch(
        rf"({_NUMBER_RE})\s*(\S+)(?:\s+(?:to|in)\s+(\S+))?",
        q,
    )
    if m:
        amount = parse_number(m.group(1))
        source = lookup_currency(m.group(2))
        target = lookup_currency(m.group(3)) if m.group(3) else None
        if source is not None and (m.group(3) is None or target is not None):
            return True, amount, source, target

    # (CURRENCY) to|in (CURRENCY)?
    m = re.fullmatch(
        r"(\S+)(?:\s+(?:to|in)\s+(\S+))?",
        q,
    )
    if m:
        source = lookup_currency(m.group(1))
        target = lookup_currency(m.group(2)) if m.group(2) else None
        if source is not None and (m.group(2) is None or target is not None):
            return True, 1.0, source, target

    return False, None, None, None


_rate_cache: dict[str, dict[str, Any]] = {}
_cache_lock = asyncio.Lock()


async def _get_rates(base: str) -> dict[str, float] | None:
    base = base.upper()
    now = time.time()

    async with _cache_lock:
        for key, entry in tuple(_rate_cache.items()):
            if entry["expires_at"] <= now:
                _rate_cache.pop(key, None)
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
