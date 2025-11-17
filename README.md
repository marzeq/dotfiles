# dotfiles

this is for my own usage, but feel free to use any of this if you want

### install 

the repo utilises `GNU stow`. make sure you install the [stow package](https://archlinux.org/packages/extra/any/stow/) and then do these commands if you want to install it on your own machine:

```bash
cd dotfiles # or wherever you cloned the repository
stow <program_name_1> <program_name_2> # ...
```

---

### automatic install script

run the `install.sh` script to stow the config files for the specified package of programs and install the necessary dependencies:

```bash
./install.sh [package]
```

**fyi - this script was made for my personal use and you should probably not run it yourself**

i recommend you instead stick to the manual install method above or use the `--dry-run` option and see what it does

---
 
### gallery

#### hyprland desktop

https://github.com/user-attachments/assets/8c3fa6c1-fb62-4822-b7b1-b3e03b1f4b3f

#### neovim

![2025-10-01-190830_hyprshot](https://github.com/user-attachments/assets/7e574460-4892-4093-9024-51c8472a38c0)
![2025-10-01-190841_hyprshot](https://github.com/user-attachments/assets/17e991b6-c1c6-4969-b2a5-1b4bd79e72b7)

---

### manual install

if you wish not to use `stow` and `install.sh`, you can find the config files for each program insie of its directory at the end of the file structure chain
(for example the config files for neovim are in `nvim/.config/nvim` because that's how stow works)

---

### notes

#### shells

the `.throwaway` file is a file for any code installed by other programs that pollutes your `.zshrc` or `.bashrc` and you want it out of there

#### hyprland customisation

edit the `hyprland-custom.conf` file to overwrite/add any custom hyprland settings you want, that way `git pull`-ing to update won't cause merge conflicts
