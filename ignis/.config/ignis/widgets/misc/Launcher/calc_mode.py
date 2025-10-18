import math
from typing import Callable
from .base_mode import LauncherMode, LauncherResult

class CalcMode(LauncherMode):
    def matches(self, query: str) -> bool:
        return query.strip().startswith("=")

    def update(self, launcher, query: str):
        expr = query.lstrip("=").strip()
        if not expr:
            launcher.result_list.child = [] # type: ignore
            return
        try:
            result = eval(expr, {"__builtins__": {
                "pi": math.pi,
                "e": math.e,
                "sqrt": lambda x: x ** 0.5,
                "pow": pow,
                "abs": abs,
                "round": round,
                "factorial": math.factorial,
                "sin": math.sin,
                "cos": math.cos,
                "tan": math.tan,
                "cot": lambda x: 1 / math.tan(x),
                "log": lambda x, base=10: math.log(x, base),
                "ln": math.log,
                "log10": math.log10,
                "log2": math.log2,
                "deg": lambda x: math.radians(x),
                "todeg": lambda x: math.degrees(x),
            }})
            if not isinstance(result, (int, float)):
                raise ValueError("Invalid result type")
            launcher.result_list.child = [
                LauncherCalcResult(result, lambda: self.launch(launcher))
            ] # type: ignore
        except Exception:
            launcher.result_list.child = [
                LauncherCalcResult(None, lambda: None)
            ] # type: ignore

    def launch(self, launcher):
        result = launcher.result_list.child[0]  # type: ignore
        if isinstance(result, LauncherCalcResult) and result.result is not None:
            launcher.set_entry_text(f"={result.result}")

class LauncherCalcResult(LauncherResult):
    def __init__(self, result: int | float | None, launch: Callable[[], None]):
        if result is None:
            super().__init__(
                label="Error",
                icon_name="dialog-warning-symbolic",
                launch=lambda: None,
                css_classes=["launcher-result-error"],
            )
            self.result = None
            return

        if result == int(result):
            result = int(result)
        elif isinstance(result, float):
            result = round(result, 10)

        super().__init__(
            label=str(result),
            icon_name="accessories-calculator-symbolic",
            launch=launch,
            css_classes=["launcher-result-value"],
        )
        self.result = result
