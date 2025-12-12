import os
import shutil
import subprocess
import hashlib
from typing import Callable
import util


class StyleManager:
    _instance = None

    @staticmethod
    def instance():
        if StyleManager._instance is None:
            StyleManager._instance = StyleManager()
        return StyleManager._instance

    def __init__(self):
        self.wallpapers_dir = os.path.expanduser("~/.wallpapers")
        os.makedirs(self.wallpapers_dir, exist_ok=True)
        self.wallpaper_symlink = os.path.join(self.wallpapers_dir, ".wallpaper")

        self.accent_cache_path = os.path.expanduser("~/.local/share/ignis/accent_map")
        os.makedirs(os.path.dirname(self.accent_cache_path), exist_ok=True)

        self.accent_map = self.load_accent_map()
        self.wallcache_dir = os.path.expanduser("~/.local/share/ignis/wallcaches")
        os.makedirs(self.wallcache_dir, exist_ok=True)

    @staticmethod
    def hash_file(path: str) -> str:
        h = hashlib.md5()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                h.update(chunk)
        return h.hexdigest()

    def load_accent_map(self):
        if not os.path.isfile(self.accent_cache_path):
            return {}
        with open(self.accent_cache_path, "r") as f:
            return {h: colour for h, colour in (line.strip().split(" ", 1) for line in f if " " in line)}

    def save_accent_map(self, accent_map):
        with open(self.accent_cache_path, "w") as f:
            for h, colour in accent_map.items():
                f.write(f"{h} {colour}\n")

    def set_accent_colour(self, colour: str, wallpaper: str):
        h = self.hash_file(wallpaper)
        self.accent_map[h] = colour
        self.save_accent_map(self.accent_map)
        self.save_lockfile()
        util.run_cmd(f"{util.root_dir}/scripts/change_accent.sh \"{colour}\"")

    def restore_accent_colour(self, wallpaper: str):
        h = self.hash_file(wallpaper)
        if h in self.accent_map:
            del self.accent_map[h]
            self.save_accent_map(self.accent_map)
        self.save_lockfile()
        util.run_cmd(f"{util.root_dir}/scripts/restore_accent.sh")

    def handle_color_chosen(self, rgba, wallpaper: str):
        hex_colour = f"#{int(rgba.red*255):02x}{int(rgba.green*255):02x}{int(rgba.blue*255):02x}"
        self.set_accent_colour(hex_colour, wallpaper)

    def set_wallpaper(self, selected_path: str):
        selected_abs = os.path.realpath(os.path.expanduser(selected_path))
        if not os.path.isfile(selected_abs):
            raise FileNotFoundError(f"File not found: {selected_abs}")

        dest_path = os.path.join(self.wallpapers_dir, os.path.basename(selected_abs))
        if not selected_abs.startswith(self.wallpapers_dir + os.sep):
            if not os.path.exists(dest_path) or not os.path.samefile(selected_abs, dest_path):
                shutil.copy2(selected_abs, dest_path)
            selected_abs = dest_path

        try:
            os.unlink(self.wallpaper_symlink)
        except FileNotFoundError:
            pass
        rel_path = os.path.relpath(selected_abs, self.wallpapers_dir)
        os.symlink(rel_path, self.wallpaper_symlink)

        subprocess.run(["pkill", "hyprpaper"], check=False)
        subprocess.run(["hyprctl", "dispatch", "exec", "hyprpaper"], check=False)

    def add_wallpaper(self, selected_path: str):
        selected_abs = os.path.realpath(os.path.expanduser(selected_path))
        if selected_abs.startswith(self.wallpapers_dir + os.sep):
            return
        dest_path = os.path.join(self.wallpapers_dir, os.path.basename(selected_abs))
        if not os.path.exists(dest_path) or not os.path.samefile(selected_abs, dest_path):
            shutil.copy2(selected_abs, dest_path)

    def get_wallpapers(self):
        wallpapers = []
        if os.path.exists(self.wallpaper_symlink):
            wallpapers.append(self.wallpaper_symlink)

        current_wallpaper = None
        if os.path.islink(self.wallpaper_symlink):
            target_abs = os.path.realpath(self.wallpaper_symlink)
            if target_abs.startswith(self.wallpapers_dir):
                current_wallpaper = os.path.relpath(target_abs, self.wallpapers_dir)
            else:
                current_wallpaper = os.path.basename(target_abs)

        for file in os.listdir(self.wallpapers_dir):
            if not file.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                continue
            if file != current_wallpaper:
                wallpapers.append(os.path.join(self.wallpapers_dir, file))

        return wallpapers

    async def get_cached_top_colours(self, path: str):
        file_hash = self.hash_file(path)
        cache_path = os.path.join(self.wallcache_dir, f"{file_hash}.cache")

        if os.path.isfile(cache_path):
            with open(cache_path, "r") as f:
                return [line.strip() for line in f if line.strip()]

        top_colours = await util.get_top_colours(path)
        with open(cache_path, "w") as f:
            f.write("\n".join(top_colours))
        return top_colours

    async def pick_wallpaper(self, file: str, refresh_callback: Callable[[], None]):
        self.set_wallpaper(file)
        refresh_callback()

        saved = self.accent_map.get(self.hash_file(file))
        if saved:
            self.save_lockfile()
            util.run_cmd(f"{util.root_dir}/scripts/change_accent.sh \"{saved}\"")
        else:
            self.save_lockfile()
            util.run_cmd(f"{util.root_dir}/scripts/restore_accent.sh")

    def has_lockfile(self) -> bool:
        return os.path.isfile("/tmp/ignis_reopen_settings")

    def save_lockfile(self):
        with open("/tmp/ignis_reopen_settings", "w") as f:
            f.write("1")

    def remove_lockfile(self):
        try:
            os.remove("/tmp/ignis_reopen_settings")
        except FileNotFoundError:
            pass

