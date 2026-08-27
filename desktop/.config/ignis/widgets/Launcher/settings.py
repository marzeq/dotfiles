import locale
import os

from util import BindableSettings, JsonSettings
from .currencies import CURRENCY_CODES


def _configured_locales() -> list[str]:
    candidates: list[str] = []

    def add(value: str | None) -> None:
        if (
            value
            and value not in ("C", "C.UTF-8", "POSIX")
            and value not in candidates
        ):
            candidates.append(value)

    current = locale.setlocale(locale.LC_MONETARY)
    add(current)
    add(os.environ.get("LC_MONETARY"))
    add(os.environ.get("LC_ALL"))
    add(os.environ.get("LANG"))

    for path in ("/etc/locale.conf", "/etc/default/locale"):
        try:
            with open(path, "r", encoding="utf-8") as locale_file:
                values: dict[str, str] = {}
                for raw_line in locale_file:
                    key, separator, value = raw_line.strip().partition("=")
                    if separator:
                        values[key] = value.strip().strip("\"'")
                add(values.get("LC_MONETARY"))
                add(values.get("LANG"))
        except OSError:
            continue

    return candidates


def infer_preferred_currency() -> str:
    original_locale = locale.setlocale(locale.LC_MONETARY)
    try:
        current_currency = locale.localeconv().get("int_curr_symbol", "").strip()
        if current_currency in CURRENCY_CODES:
            return current_currency

        for locale_name in _configured_locales():
            try:
                locale.setlocale(locale.LC_MONETARY, locale_name)
            except locale.Error:
                continue
            currency = locale.localeconv().get("int_curr_symbol", "").strip()
            if currency in CURRENCY_CODES:
                return currency
    finally:
        locale.setlocale(locale.LC_MONETARY, original_locale)

    return "USD"


@JsonSettings("launcher")
class LauncherSettings(BindableSettings):
    preferred_currency: str = infer_preferred_currency()
    calculator_enabled: bool = True
    currency_enabled: bool = True
    power_actions_enabled: bool = True

    def set_preferred_currency(self, currency: str):
        self.preferred_currency = currency

    def set_calculator_enabled(self, enabled: bool) -> None:
        self.calculator_enabled = enabled

    def set_currency_enabled(self, enabled: bool) -> None:
        self.currency_enabled = enabled

    def set_power_actions_enabled(self, enabled: bool) -> None:
        self.power_actions_enabled = enabled


launcher_settings = LauncherSettings()
