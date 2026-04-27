#!/usr/bin/env bash
set -e

RED_BOLD="\033[1;31m"
BLUE="\033[0;34m"
GREEN_BOLD="\033[1;32m"
RESET="\033[0m"

error() {
  echo -e "${RED_BOLD}$1${RESET}" >&2
  exit 1
}

info() {
  echo -e "${BLUE}$1${RESET}"
}

if [[ $EUID -eq 0 ]]; then
  error "Don't run this script as root."
fi

local_share_path="$HOME/.local/share/marzeq/dotfiles"
state_dir="$HOME/.local/share/marzeq"
cli_target="$HOME/.local/bin/marzeq-dotfiles"

if ! command -v git &>/dev/null; then
  error "git is required to bootstrap dotfiles."
fi

mkdir -p "$(dirname "$local_share_path")" "$state_dir" "$(dirname "$cli_target")"

cwd="$(pwd)"
if [[ -d "$cwd/.git" && ! -d "$local_share_path" ]]; then
  origin_url="$(git -C "$cwd" config --get remote.origin.url 2>/dev/null || true)"
  if [[ "$origin_url" == *"marzeq/dotfiles"* ]]; then
    info "Detected local clone in current directory; linking into $local_share_path"
    ln -sfn "$cwd" "$local_share_path"
  fi
fi

if [[ -d "$local_share_path/.git" ]]; then
  info "Updating existing dotfiles repository..."
  git -C "$local_share_path" pull --ff-only || error "Failed to update repository."
else
  info "Cloning dotfiles repository to $local_share_path..."
  git clone "https://github.com/marzeq/dotfiles.git" "$local_share_path" || error "Git clone failed."
fi


if [[ -f "$local_share_path/marzeq-dotfiles" ]]; then
  info "Linking CLI to $cli_target"
  chmod +x "$local_share_path/marzeq-dotfiles" || true
  ln -sf "$local_share_path/marzeq-dotfiles" "$cli_target"
else
  info "Warning: CLI script not found in repository; skipping link."
fi


info "Bootstrap complete. Repo path: $local_share_path"

echo
echo "Run '$cli_target --help' to see available commands for managing the installation."
