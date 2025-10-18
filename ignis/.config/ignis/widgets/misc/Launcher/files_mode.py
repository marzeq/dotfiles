from rapidfuzz import process, fuzz
import subprocess
import os
import util

from .base_mode import LauncherMode, LauncherResult

class FilesMode(LauncherMode):
    def matches(self, query: str) -> bool:
        return query.startswith("/") or query.startswith("~")

    def update(self, launcher, query: str):
        prompt = query.strip()
        show_hidden = False

        if prompt.startswith("~~"):
            show_hidden = True
            prompt = "~" + prompt[2:] if prompt[2:2+1] == "/" else "~/" + prompt[2:].lstrip("/")
        elif prompt.startswith("//"):
            show_hidden = True
            prompt = "/" + prompt[2:] if prompt[2:2+1] == "/" else "/" + prompt[2:].lstrip("/")

        path = os.path.expanduser(prompt)

        if os.path.exists(path) and os.path.isdir(path):
            display_name = path
            if prompt.startswith("~"):
                display_name = "~" + path[len(os.path.expanduser("~")):]

            results = [LauncherFileResult(path, display_name=display_name)]

            try:
                for entry in sorted(os.listdir(path)):
                    if entry.startswith(".") and not show_hidden:
                        continue
                    full_path = os.path.join(path, entry)
                    results.append(LauncherFileResult(full_path))
            except Exception:
                pass

            launcher.result_list.child = results  # type: ignore
            return

        parent, basename = os.path.split(path)
        if not parent or not os.path.exists(parent) or not os.path.isdir(parent):
            launcher.result_list.child = []  # type: ignore
            return

        try:
            entries = os.listdir(parent)
        except Exception:
            launcher.result_list.child = []  # type: ignore
            return

        filtered_entries = []
        for e in entries:
            full_path = os.path.join(parent, e)
            if e.startswith(".") and not show_hidden and e != basename:
                continue
            filtered_entries.append(e)

        matches = process.extract(
            basename,
            filtered_entries,
            scorer=fuzz.WRatio,
            limit=10,
            score_cutoff=60,
        )
        if not matches:
            launcher.result_list.child = []  # type: ignore
            return

        launcher.result_list.child = [
            LauncherFileResult(os.path.join(parent, match[0])) for match in matches
        ]  # type: ignore

    def launch(self, launcher):
        if launcher.result_list.child:
            launcher.result_list.child[0].on_click()  # type: ignore

class LauncherFileResult(LauncherResult):
    def __init__(self, path: str, display_name: str | None = None):
        name = display_name or os.path.basename(path) or path
        icon_name = "text-x-generic" if os.path.isfile(path) else "folder"
        super().__init__(
            label=name,
            icon_name=icon_name,
            launch=lambda: self.launch_file(),
            css_classes=["launcher-result-file"],
        )
        self.path = path

    def launch_file(self):
        subprocess.Popen(["xdg-open", self.path])
        util.close_curr_popup()

