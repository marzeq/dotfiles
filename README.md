# dotfiles

this is for my own usage, but feel free to use any of this if you want

### install 

the repo utilises `GNU stow`. make sure you install the [stow package](https://archlinux.org/packages/extra/any/stow/) and then do these commands if you want to install it on your own machine:

```bash
cd dotfiles # or wherever you cloned the repository
stow <program_name_1> <program_name_2> # ...
# for example: stow nvim/ ghostty/
```

---

### automatic install script

**fyi - this script was made for my personal use and you should probably not run it yourself**

run the `install.sh` script to stow the config files for the specified package of programs and install the necessary dependencies:

```bash
./install.sh [package]
# Available packages: shells, neovim, terminal, desktop, fonts, gaming
# Or run ./install.sh all to install all packages
```

---
 
### gallery

#### hyprland desktop

incredibly gnome inspired

<img width="2560" height="1440" alt="image" src="https://github.com/user-attachments/assets/e7c42e54-3455-4e6a-9805-6a37f3ee414a" />
<img width="2560" height="1440" alt="image" src="https://github.com/user-attachments/assets/f4d82f3c-59b4-4cbf-82f2-4c0799b9984d" />
<img width="2560" height="1440" alt="image" src="https://github.com/user-attachments/assets/921a80c6-3a19-45b2-96f7-621a83e782d0" />
<img width="2560" height="1440" alt="image" src="https://github.com/user-attachments/assets/f0fecaff-34b1-4bf5-aabe-eed3badc0f82" />


#### neovim

![image](https://github.com/user-attachments/assets/f151193e-d46d-471c-9d9c-4c696212737c)

![image](https://github.com/user-attachments/assets/5d1d52ee-2fea-4b1d-83c5-08c044612bf2)

---

### manual install

if you wish not to use `stow` and `install.sh`, you can find the config files for each program insie of its directory at the end of the file structure chain
(for example the config files for neovim are in `nvim/.config/nvim` because that's how stow works)

---

### notes

#### shells

the `.throwaway` file is a file for any code installed by other programs that pollutes your `.zshrc` or `.bashrc` and you want it out of there
