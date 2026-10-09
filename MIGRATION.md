# Migrating to the management CLI

Use this guide only if you installed an older version of these dotfiles by cloning the repository and running
`./install.sh [component]`. New installations should follow [INSTALL.md](./INSTALL.md) instead.

> **Do not run the remote bootstrap command from `INSTALL.md`.** It may create a new clone and break the paths used by
> your existing GNU Stow links.

## 1. Update the existing clone

Open the repository you originally installed and pull the latest changes:

```bash
cd /path/to/your/existing/dotfiles
git pull
```

## 2. Run the local bootstrap

```bash
./install.sh
```

The bootstrap detects that it is running inside the existing clone. It links that clone to
`~/.local/share/marzeq/dotfiles` and installs the management CLI at `~/.local/bin/marzeq-dotfiles` without replacing the
repository behind your existing Stow links.

## 3. Register the components you already use

Run the install command with the components from your old installation. For example:

```bash
marzeq-dotfiles install shells nvim
```

The command is idempotent: it reapplies those components and records them for future management. Afterwards you can use
`marzeq-dotfiles update`, `list` and `remove` normally while keeping the original clone and Stow paths intact.
