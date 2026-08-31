# Long-running memory profiling

The shell has an opt-in profiler that records both Python allocations and the
Linux process memory counters. It is off by default because `tracemalloc` adds
CPU and memory overhead.

Start Ignis from the same place you normally do, adding this environment
variable:

```sh
IGNIS_MEMORY_PROFILE=1 ignis init
```

If Ignis is started by a user systemd service, add this to the service instead:

```ini
Environment=IGNIS_MEMORY_PROFILE=1
```

Reports are appended every 10 minutes to:

```text
~/.local/state/ignis/memory-profile.log
```

Useful optional settings:

```sh
IGNIS_MEMORY_PROFILE_INTERVAL=300   # seconds; minimum 10
IGNIS_MEMORY_PROFILE_FRAMES=8       # traceback depth; higher costs more RAM
IGNIS_MEMORY_PROFILE_TOP=30         # entries in each report
IGNIS_MEMORY_PROFILE_LOG=/tmp/ignis-memory.log
```

To request a report immediately, send `SIGUSR1` to the Ignis Python process.

## Reading the report

- If `VmRSS`/`Pss` and `tracemalloc current` rise together, inspect the listed
  Python file and line allocation growth.
- If `VmRSS`/`Pss` rises while `tracemalloc current` remains mostly flat, the
  growth is native memory (commonly GTK, GObject, pixbufs, or a C extension),
  not allocations owned directly by Python.
- Repeated growth of one GC-tracked object type points to signal handlers,
  callbacks, tasks, or widgets retaining those objects.
- Each report compares with the preceding report, not with process startup, so
  a continuously leaking line stays visible instead of being drowned out by
  normal startup allocations.

Leave it enabled through the period that normally reaches high memory, then
compare several consecutive reports. Do not judge from only the first report:
it is intentionally just the baseline.
