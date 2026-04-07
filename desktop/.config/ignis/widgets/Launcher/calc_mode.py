import util
import shlex
from .base_mode import LauncherMode, LauncherResult
import platform


class CalcMode(LauncherMode):
    def build(self, launcher):
        super().build(launcher)
        self.set_results([LauncherCalcResult("", lambda: self.launch())])
        self.results[0].visible = False
        self.section.visible = False
        return self.section

    async def update(self, query: str, refresh):
        result_widget = self.results[0]
        expr = query.strip()
        if not expr:
            result_widget.visible = False
            self.section.visible = False
            refresh()
            return

        exname = ""
        match platform.machine():
            case "x86_64":
                exname = "mexe-amd64"
            case "aarch64":
                exname = "mexe-aarch64"
            case _:
                return

        escaped_expr = shlex.quote(expr)
        result = await util.shell(
            f"{util.root_dir}/scripts/{exname} -- {escaped_expr}",
            background=False,
        )
        if result is None:
            result_widget.visible = False
            self.section.visible = False
            refresh()
            return

        result_widget.set_value(result)
        result_widget.visible = True
        self.section.visible = True
        refresh()

    def launch(self):
        if not self.results:
            return

        result = self.results[0]
        if isinstance(result, LauncherCalcResult) and result.result is not None:
            if self.launcher is not None:
                self.launcher.set_entry_text(f"{result.result}")


class LauncherCalcResult(LauncherResult):
    def __init__(self, result: str, launch):
        super().__init__(
            value=result,
            icon_name="accessories-calculator-symbolic",
            launch=launch,
            css_classes=["launcher-result-value"],
        )
        self.result = result
