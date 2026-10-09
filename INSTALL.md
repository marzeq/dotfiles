# Installation and management

The managed installer is the recommended route for most users. It installs dependencies, applies only the components you
choose and remembers them for future updates or removal.

> The managed path requires Arch Linux x86-64. Advanced users on another distribution or macOS should use the separate
> [manual installation guide](./ADVANCED.md).

## Managed installation (recommended)

The CLI installs the relevant pacman and AUR dependencies, Stows the managed components you select and their declared
dependencies, and records that selection so it can update or remove them later.

Prerequisites:

- A working `git` installation.
- You are on Arch Linux (this repo and scripts assume `pacman` + AUR tooling).
- Your system uses the x86-64 architecture.
- `~/.local/bin` is on your `PATH` (the bootstrap links the CLI there).

### Bootstrap (one-time)

The bootstrap script will handle cloning the repo, setting up the CLI tool, and ensuring you have a way to manage the dotfiles going forward.

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

At this point, the dotfiles are set up to be installed, but no components are applied yet. Use the CLI to manage installation and updates.

## Managing your install

Alongside the actual dotfiles, we provide a CLI tool to manage installation and updates. The CLI is idempotent and safe to run multiple times.

### install

Use `marzeq-dotfiles install` to install one or more components. 
It's best to preview with `--dry-run` first to see exactly which commands will make changes to your system.

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

Installing `desktop` also installs `terminal`, which is part of the desktop setup.

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

## Other paths

- Already using an older version of these dotfiles? Follow the [migration guide](./MIGRATION.md).
- Using another distribution or macOS, or prefer to manage everything yourself? Follow the
  [advanced manual installation guide](./ADVANCED.md).
