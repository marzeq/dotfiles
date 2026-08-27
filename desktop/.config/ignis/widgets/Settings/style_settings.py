import os
import hashlib
import json
import util
from util import JsonSettings, BindableSettings


@JsonSettings("style")
class StyleSettings(BindableSettings):
    wallpaper: str = os.path.expanduser("~/.config/ignis/default_wallpaper.jpg")
    addedwallpapers: str = ""
    custom_accent_colours: str = ""

    def __init__(self):
        super().__init__()

        self._accent_cache_path = os.path.expanduser("~/.local/share/ignis/accent_map")
        os.makedirs(os.path.dirname(self._accent_cache_path), exist_ok=True)

        self._wallcache_dir = os.path.expanduser("~/.local/share/ignis/wallcaches")
        os.makedirs(self._wallcache_dir, exist_ok=True)

        self._accent_map = self._load_accent_map()

    post_accent_change_cmd: str = ""

    def set_post_accent_change_cmd(self, cmd: str):
        self.post_accent_change_cmd = cmd

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

    def get_accent_colour(self, wallpaper: str) -> str | None:
        return self._accent_map.get(self._hash_file(wallpaper))

    def _get_custom_accent_map(self) -> dict[str, list[str]]:
        raw = self.custom_accent_colours.strip()
        if not raw:
            return {}
        try:
            loaded = json.loads(raw)
            if isinstance(loaded, dict):
                return {
                    str(wallpaper_hash): [
                        str(colour).lower() for colour in colours
                    ]
                    for wallpaper_hash, colours in loaded.items()
                    if isinstance(colours, list)
                }
        except (json.JSONDecodeError, TypeError):
            pass

        # Migrate the previous global semicolon-delimited list to the wallpaper
        # that was active when this version first reads it.
        legacy_colours = [colour.lower() for colour in raw.split(";") if colour]
        migrated = {self._hash_file(self.wallpaper): legacy_colours}
        self._save_custom_accent_map(migrated)
        return migrated

    def _save_custom_accent_map(self, accent_map: dict[str, list[str]]) -> None:
        self.custom_accent_colours = json.dumps(
            accent_map, separators=(",", ":"), sort_keys=True
        )

    def list_custom_accent_colours(self, wallpaper: str) -> list[str]:
        return list(self._get_custom_accent_map().get(self._hash_file(wallpaper), []))

    def add_custom_accent_colour(self, colour: str, wallpaper: str) -> None:
        colour = colour.lower()
        accent_map = self._get_custom_accent_map()
        wallpaper_hash = self._hash_file(wallpaper)
        colours = accent_map.setdefault(wallpaper_hash, [])
        if colour not in colours:
            colours.append(colour)
            self._save_custom_accent_map(accent_map)

    def remove_custom_accent_colour(self, colour: str, wallpaper: str) -> None:
        colour = colour.lower()
        accent_map = self._get_custom_accent_map()
        wallpaper_hash = self._hash_file(wallpaper)
        colours = [
            saved_colour
            for saved_colour in accent_map.get(wallpaper_hash, [])
            if saved_colour.lower() != colour
        ]
        if colours:
            accent_map[wallpaper_hash] = colours
        else:
            accent_map.pop(wallpaper_hash, None)
        self._save_custom_accent_map(accent_map)

    async def post_accent_change(self):
        util.get_app().reload_css()
        if self.post_accent_change_cmd:
            await util.shell(self.post_accent_change_cmd, background=False)

    def set_accent_colour(self, colour: str, wallpaper: str):
        h = self._hash_file(wallpaper)
        self._accent_map[h] = colour
        self._save_accent_map()
        util.shell(
            f'{util.root_dir}/scripts/change_accent.sh "{colour}"',
            after=self.post_accent_change,
        )

    def restore_accent_colour(self, wallpaper: str):
        h = self._hash_file(wallpaper)
        if h in self._accent_map:
            del self._accent_map[h]
            self._save_accent_map()
        util.shell(
            f"{util.root_dir}/scripts/restore_accent.sh",
            after=self.post_accent_change,
        )

    def add_custom_accent_colour_from_rgba(self, rgba, wallpaper: str) -> None:
        self.add_custom_accent_colour(
            f"#{int(rgba.red * 255):02x}"
            f"{int(rgba.green * 255):02x}"
            f"{int(rgba.blue * 255):02x}",
            wallpaper,
        )

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

    def remove_wallpaper(self, path: str):
        abs_path = os.path.realpath(os.path.expanduser(path))
        file_hash = self._hash_file(abs_path) if os.path.isfile(abs_path) else None
        current_list = self._added_wallpapers_str_to_list(self.addedwallpapers)
        if abs_path in current_list:
            current_list.remove(abs_path)
            self.addedwallpapers = self._added_wallpapers_list_to_str(current_list)
        if file_hash is not None:
            if self._accent_map.pop(file_hash, None) is not None:
                self._save_accent_map()
            try:
                os.remove(os.path.join(self._wallcache_dir, f"{file_hash}.cache"))
            except FileNotFoundError:
                pass

    def get_wallpapers(self):
        wallpapers: list[str] = []

        for path in self._added_wallpapers_str_to_list(self.addedwallpapers):
            if os.path.isfile(path) and path.endswith(
                (".jpg", ".jpeg", ".png", ".webp")
            ):
                wallpapers.append(path)

        return wallpapers

    async def get_cached_top_colours(self, path: str):
        file_hash = self._hash_file(path)
        cache_path = os.path.join(self._wallcache_dir, f"{file_hash}.cache")

        if os.path.isfile(cache_path):
            with open(cache_path, "r") as f:
                return [line.strip() for line in f if line.strip()]

        top_colours = await util.get_top_colours(path)
        with open(cache_path, "w") as f:
            f.write("\n".join(top_colours))
        return top_colours

    async def pick_wallpaper(self, file: str):
        self.set_wallpaper(file)
        util.shell("~/.config/hypr/scripts/set_curr_wallpaper.sh")

        saved = self._accent_map.get(self._hash_file(self.wallpaper))
        if saved:
            util.shell(
                f'{util.root_dir}/scripts/change_accent.sh "{saved}"',
                after=self.post_accent_change,
            )
        else:
            util.shell(
                f"{util.root_dir}/scripts/restore_accent.sh",
                after=self.post_accent_change,
            )


style_settings = StyleSettings()
