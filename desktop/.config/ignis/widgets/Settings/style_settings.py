import asyncio
import os
import hashlib
import util
from util import JsonSettings, BindableSettings


async def recompile_css():
    await asyncio.sleep(0.01)
    util.get_app().reload_css()


@JsonSettings("style")
class StyleSettings(BindableSettings):
    wallpaper: str = os.path.expanduser("~/.config/ignis/default_wallpaper.jpg")
    addedwallpapers: str = ""

    def __init__(self):
        super().__init__()

        self._accent_cache_path = os.path.expanduser(
            "~/.local/share/ignis/accent_map"
        )
        os.makedirs(os.path.dirname(self._accent_cache_path), exist_ok=True)

        self._wallcache_dir = os.path.expanduser(
            "~/.local/share/ignis/wallcaches"
        )
        os.makedirs(self._wallcache_dir, exist_ok=True)

        self._accent_map = self._load_accent_map()

    def _hash_file(self, path: str) -> str:
        h = hashlib.md5()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                h.update(chunk)
        return h.hexdigest()

    def _load_accent_map(self):
        if not os.path.isfile(self._accent_cache_path):
            return {}
        with open(self._accent_cache_path, "r") as f:
            return {
                h: colour
                for h, colour in (
                    line.strip().split(" ", 1) for line in f if " " in line
                )
            }

    def _save_accent_map(self):
        with open(self._accent_cache_path, "w") as f:
            for h, colour in self._accent_map.items():
                f.write(f"{h} {colour}\n")

    def set_accent_colour(self, colour: str, wallpaper: str):
        h = self._hash_file(wallpaper)
        self._accent_map[h] = colour
        self._save_accent_map()
        asyncio.create_task(
            util.run_cmd_async(
                f'{util.root_dir}/scripts/change_accent.sh "{colour}"',
                awaitable=recompile_css(),
            )
        )

    def restore_accent_colour(self, wallpaper: str):
        h = self._hash_file(wallpaper)
        if h in self._accent_map:
            del self._accent_map[h]
            self._save_accent_map()
        asyncio.create_task(
            util.run_cmd_async(
                f"{util.root_dir}/scripts/restore_accent.sh",
                awaitable=recompile_css(),
            )
        )

    def handle_color_chosen(self, rgba, wallpaper: str):
        hex_colour = (
            f"#{int(rgba.red * 255):02x}"
            f"{int(rgba.green * 255):02x}"
            f"{int(rgba.blue * 255):02x}"
        )
        self.set_accent_colour(hex_colour, wallpaper)

    def _added_wallpapers_str_to_list(self, s: str):
        parts = []
        current = []
        i = 0
        while i < len(s):
            if s[i] == ";":
                if i + 1 < len(s) and s[i + 1] == ";":
                    current.append(";")
                    i += 2
                else:
                    parts.append("".join(current))
                    current = []
                    i += 1
            else:
                current.append(s[i])
                i += 1
        if current:
            parts.append("".join(current))
        return [part for part in parts if part]

    def _added_wallpapers_list_to_str(self, lst):
        parts = []
        for path in lst:
            escaped = path.replace(";", ";;")
            parts.append(escaped)
        return ";".join(parts)

    def set_wallpaper(self, path: str):
        abs_path = os.path.realpath(os.path.expanduser(path))
        if not os.path.isfile(abs_path):
            raise FileNotFoundError(f"File not found: {abs_path}")

        self.wallpaper = abs_path

    def add_wallpaper(self, path: str):
        abs_path = os.path.realpath(os.path.expanduser(path))
        if not os.path.isfile(abs_path):
            raise FileNotFoundError(f"File not found: {abs_path}")

        current_list = self._added_wallpapers_str_to_list(self.addedwallpapers)
        if abs_path not in current_list:
            current_list.append(abs_path)
            self.addedwallpapers = self._added_wallpapers_list_to_str(current_list)

    def get_wallpapers(self):
        wallpapers: list[str] = []

        current = (
            os.path.realpath(self.wallpaper)
            if self.wallpaper and os.path.isfile(self.wallpaper)
            else None
        )
        if current:
            wallpapers.append(current)

        for path in self._added_wallpapers_str_to_list(self.addedwallpapers):
            if path != current and os.path.isfile(path) and path.endswith((".jpg", ".jpeg", ".png", ".webp")):
                wallpapers.append(path)

        return wallpapers

    async def get_cached_top_colours(self, path: str):
        file_hash = self._hash_file(path)
        cache_path = os.path.join(
            self._wallcache_dir, f"{file_hash}.cache"
        )

        if os.path.isfile(cache_path):
            with open(cache_path, "r") as f:
                return [line.strip() for line in f if line.strip()]

        top_colours = await util.get_top_colours(path)
        with open(cache_path, "w") as f:
            f.write("\n".join(top_colours))
        return top_colours

    async def pick_wallpaper(
        self, file: str
    ):
        self.set_wallpaper(file)
        util.run_cmd("~/.config/hypr/scripts/set_curr_wallpaper.sh")

        saved = self._accent_map.get(self._hash_file(self.wallpaper))
        if saved:
            asyncio.create_task(
                util.run_cmd_async(
                    f'{util.root_dir}/scripts/change_accent.sh "{saved}"',
                    awaitable=recompile_css(),
                )
            )
        else:
            asyncio.create_task(
                util.run_cmd_async(
                    f"{util.root_dir}/scripts/restore_accent.sh",
                    awaitable=recompile_css(),
                )
            )


style_settings = StyleSettings()
