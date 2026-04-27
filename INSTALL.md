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

## Migration from an old dotfiles setup

If you have installed these dotfiles using the old method (clone and `./install.sh [component]`), you can perform a migration with the instructions below.

**IMPORTANT:**

When migrating, *DO NOT* wget the bootstrap script, as it will re-clone the repo and the CLI tool will break existing stow links. 
Instead *PLEASE DO* follow the exact steps below to avoid issues:

1. Pull latest changes to the repo to obtain the new bootstrap and management script:

```bash
cd (wherever you cloned the repo)
git pull
```

2. Run the boostrap script:

```bash
./install.sh
```

The boostrap script will detect that it lives inside the repo and will not re-clone,
but it will link it to `~/.local/share/marzeq/dotfiles` and install the CLI tool to `~/.local/bin/marzeq-dotfiles`.

This is to not break the existing stow links and allow you to immediately use the new CLI tool to manage your install going forward.

3. Manually add the components you have previously installed to the CLI's tracking:

```bash
# example if you had shells and nvim previously installed
marzeq-dotfiles install shells nvim
```

After this, the CLI will be aware of the components you have installed and you can use it to manage updates and future installs/removals as normal,
but the actual repo location and stow links will remain intact and not break.
