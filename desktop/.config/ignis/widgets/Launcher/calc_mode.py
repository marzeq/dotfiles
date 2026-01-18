from typing import Callable

import util
import shlex
from .base_mode import LauncherMode, LauncherResult


class CalcMode(LauncherMode):
    async def get_results(self, launcher, query, emit):
        expr = query.strip()
        if not expr:
            return

        escaped_expr = shlex.quote(expr)
        result = await util.shell(
            f"{util.root_dir}/scripts/mexe -- {escaped_expr}",
            background=False,
        )
        if result is None:
            return

        emit(
            [LauncherCalcResult(result, lambda: self.launch(launcher))],
            False,
        )

    def launch(self, launcher):
        result = launcher.get_results()[0]
        if isinstance(result, LauncherCalcResult) and result.result is not None:
            launcher.set_entry_text(f"{result.result}")


class LauncherCalcResult(LauncherResult):
    def __init__(self, result: str, launch: Callable[[], None]):
        super().__init__(
            value=result,
            icon_name="accessories-calculator-symbolic",
            launch=launch,
            css_classes=["launcher-result-value"],
        )
        self.result = result
