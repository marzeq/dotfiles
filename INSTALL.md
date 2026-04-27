# Installation and management

Prerequisites

- A working `git` installation.
- You are on Arch Linux (this repo and scripts assume `pacman` + AUR tooling).
- `~/.local/bin` is on your `PATH` (the bootstrap links the CLI there).

## Bootstrap (one-time)

The bootstrap script will handle cloning the repo, setting up the CLI tool, and ensuring you have a way to manage your dotfiles going forward.

1. Run the bootstrap script:

```bash
wget -q -O - https://raw.githubusercontent.com/marzeq/dotfiles/refs/heads/dev/install.sh | bash
```

What this does:
- clones the repo to `~/.local/share/marzeq/dotfiles` if not present
- pulls updates if it is present
- creates a symlink from `~/.local/share/marzeq/dotfiles/marzeq-dotfiles` → `~/.local/bin/marzeq-dotfiles`

Verify bootstrap:

```bash
ls -l ~/.local/share/marzeq/dotfiles
ls -l ~/.local/bin/marzeq-dotfiles
marzeq-dotfiles --help
```

At this point, the dotfiles are setup to be installed, but no components are applied yet. Use the CLI to manage installation and updates.

## Managing your install

Alongside the actual dotfiles, we provide a CLI tool to manage installation and updates. The CLI is idempotent and safe to run multiple times.

### install

Use `marzeq-dotfiles install` to install one or more components. 
It's best to preview with `--dry-run` first to see exactly what commands will be ran that will make changes to your system.

Examples:

```bash
# preview an install
marzeq-dotfiles --dry-run install shells

# install a single component
marzeq-dotfiles install shells

# install multiple components
marzeq-dotfiles install shells nvim

# install everything
marzeq-dotfiles install all
```

### update

Pulls the latest repo and re-applies only the components you previously installed.

```bash
marzeq-dotfiles update
```

To update without re-installing packages:

```bash
marzeq-dotfiles update --skip-packages
```

You can also use `--dry-run` with update.

### list

Show which components are recorded as installed.

```bash
marzeq-dotfiles list
```

### remove

Unstow and forget a component.

```bash
marzeq-dotfiles remove shells
marzeq-dotfiles remove all
```

### Quick safety checklist

- Preview with `--dry-run` before running installs.
- Back up any local files you care about before applying changes.

### Troubleshooting

- If the CLI is not found, ensure `~/.local/bin` is on your `PATH`.
- If the repo path is wrong, re-run the bootstrap
