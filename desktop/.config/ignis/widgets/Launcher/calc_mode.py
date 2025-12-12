import math
from typing import Callable
from .base_mode import GetResultsResponse, LauncherMode, LauncherResult

class CalcMode(LauncherMode):
    def get_results(self, launcher, query: str):
        expr = query.strip()
        if not expr:
            return GetResultsResponse([])
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
                return GetResultsResponse([])
            return GetResultsResponse([LauncherCalcResult(result, lambda: self.launch(launcher))], False)
        except Exception:
            return GetResultsResponse([], False)

    def launch(self, launcher):
        result = launcher.get_results()[0]
        if isinstance(result, LauncherCalcResult) and result.result is not None:
            launcher.set_entry_text(f"{result.result}")

class LauncherCalcResult(LauncherResult):
    def __init__(self, result: int | float, launch: Callable[[], None]):
        if result == int(result):
            result = int(result)
        elif isinstance(result, float):
            result = round(result, 10)

        super().__init__(
            value=str(result),
            icon_name="accessories-calculator-symbolic",
            launch=launch,
            css_classes=["launcher-result-value"],
        )
        self.result = result
