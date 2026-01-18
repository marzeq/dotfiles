from util import BindableSettings, JsonSettings


@JsonSettings("launcher")
class LauncherSettings(BindableSettings):
    preferred_currency: str = "USD"

    def set_preferred_currency(self, currency: str):
        self.preferred_currency = currency


launcher_settings = LauncherSettings()
