"""Opt-in, long-running memory diagnostics for the Ignis shell.

Enable with ``IGNIS_MEMORY_PROFILE=1`` before starting Ignis.  The profiler is
deliberately implemented using only the standard library so it is safe to
leave running on a machine where installing debug packages is inconvenient.
"""

from __future__ import annotations

import asyncio
import gc
import os
import signal
import sys
import time
import tracemalloc
from collections import Counter
from pathlib import Path
from typing import TextIO


_started = False
_snapshot: tracemalloc.Snapshot | None = None
_type_counts: Counter[str] | None = None
_dump_event: asyncio.Event | None = None


def _positive_int(name: str, default: int, minimum: int) -> int:
    try:
        return max(minimum, int(os.environ.get(name, default)))
    except ValueError:
        return default


def _memory_status() -> dict[str, int]:
    """Return Linux process memory counters in KiB when available."""
    result: dict[str, int] = {}
    try:
        with open("/proc/self/status", encoding="utf-8") as status:
            for line in status:
                key, _, value = line.partition(":")
                if key in {"VmRSS", "VmSize", "RssAnon", "RssFile"}:
                    result[key] = int(value.strip().split()[0])
        with open("/proc/self/smaps_rollup", encoding="utf-8") as smaps:
            for line in smaps:
                key, _, value = line.partition(":")
                if key in {"Pss", "Private_Clean", "Private_Dirty"}:
                    result[key] = int(value.strip().split()[0])
    except (OSError, ValueError, IndexError):
        pass
    return result


def _object_counts() -> Counter[str]:
    return Counter(
        f"{type(obj).__module__}.{type(obj).__qualname__}" for obj in gc.get_objects()
    )


def _format_kib(value: int) -> str:
    return f"{value / 1024:.1f} MiB"


def _write_stats(
    output: TextIO,
    title: str,
    stats: list[tracemalloc.StatisticDiff],
    limit: int,
) -> None:
    output.write(f"\n{title}\n")
    shown = 0
    for stat in stats:
        # Negative entries are useful for accounting but not for finding growth.
        if stat.size_diff <= 0:
            continue
        frame = stat.traceback[0]
        output.write(
            f"  +{stat.size_diff / 1024:.1f} KiB "
            f"(+{stat.count_diff} blocks) {frame.filename}:{frame.lineno}\n"
        )
        shown += 1
        if shown >= limit:
            break
    if shown == 0:
        output.write("  (no positive Python allocation growth)\n")


def _dump(log_path: Path, project_root: Path, reason: str, top: int) -> None:
    global _snapshot, _type_counts

    # Collect immediately before measuring so unreachable cycles do not look
    # like a leak. This does not free live GTK/GObject references.
    gc.collect()
    current = tracemalloc.take_snapshot()
    current_counts = _object_counts()
    traced_current, traced_peak = tracemalloc.get_traced_memory()
    memory = _memory_status()

    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as output:
        output.write("\n" + "=" * 78 + "\n")
        output.write(
            f"{time.strftime('%Y-%m-%d %H:%M:%S %z')} reason={reason} "
            f"pid={os.getpid()} uptime={time.monotonic():.0f}s\n"
        )
        output.write(
            "process: "
            + " ".join(f"{key}={_format_kib(value)}" for key, value in memory.items())
            + "\n"
        )
        output.write(
            f"tracemalloc: current={_format_kib(traced_current // 1024)} "
            f"peak={_format_kib(traced_peak // 1024)}\n"
        )

        if _snapshot is None:
            output.write("This is the baseline snapshot; growth starts at the next dump.\n")
        else:
            all_growth = current.compare_to(_snapshot, "lineno")
            project_growth = [
                stat
                for stat in all_growth
                if str(project_root) in stat.traceback[0].filename
            ]
            _write_stats(output, "Python growth in this config:", project_growth, top)
            _write_stats(output, "Python growth across all modules:", all_growth, top)

        if _type_counts is not None:
            output.write("\nGC-tracked object type growth:\n")
            growth = current_counts - _type_counts
            for name, count in growth.most_common(top):
                output.write(f"  +{count} {name}\n")
            if not growth:
                output.write("  (no positive object-count growth)\n")

        output.flush()

    # Retain only one snapshot/count set: memory use stays bounded and each
    # report describes growth during the most recent interval.
    _snapshot = current
    _type_counts = current_counts


async def _run(log_path: Path, project_root: Path, interval: int, top: int) -> None:
    _dump(log_path, project_root, "startup baseline", top)
    while True:
        assert _dump_event is not None
        try:
            await asyncio.wait_for(_dump_event.wait(), timeout=interval)
            reason = "SIGUSR1"
            _dump_event.clear()
        except TimeoutError:
            reason = "periodic"
        _dump(log_path, project_root, reason, top)


def start(project_root: str) -> asyncio.Task[None] | None:
    """Start the profiler once, returning its asyncio task when enabled."""
    global _started, _dump_event
    if _started or os.environ.get("IGNIS_MEMORY_PROFILE") != "1":
        return None
    _started = True

    interval = _positive_int("IGNIS_MEMORY_PROFILE_INTERVAL", 600, 10)
    frames = _positive_int("IGNIS_MEMORY_PROFILE_FRAMES", 8, 1)
    top = _positive_int("IGNIS_MEMORY_PROFILE_TOP", 30, 1)
    default_log = Path.home() / ".local/state/ignis/memory-profile.log"
    log_path = Path(os.environ.get("IGNIS_MEMORY_PROFILE_LOG", default_log)).expanduser()
    root = Path(project_root).resolve()

    tracemalloc.start(frames)
    _dump_event = asyncio.Event()

    def request_dump(_signum: int, _frame: object) -> None:
        # Snapshot work happens in the asyncio task, outside the signal handler.
        assert _dump_event is not None
        _dump_event.set()

    if hasattr(signal, "SIGUSR1"):
        signal.signal(signal.SIGUSR1, request_dump)

    print(
        f"Ignis memory profiling enabled: {log_path} (every {interval}s)",
        file=sys.stderr,
    )
    return asyncio.create_task(_run(log_path, root, interval, top))
