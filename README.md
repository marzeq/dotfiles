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

run the `install.sh` script to stow the config files for the specified package of programs and install the necessary dependencies:

```bash
./install.sh [package]
# packages: shells, neovim, ghostty, hyprland, fonts, gaming
# or `all` to install all packages
```

---
 
### gallery

#### hyprland desktop

![image](https://github.com/user-attachments/assets/0283f725-00c0-4a56-be03-f481b61e7cce)

#### neovim

![image](https://github.com/user-attachments/assets/ae1c454a-9351-4f3e-9228-a4f8d15b94af)

![image](https://github.com/user-attachments/assets/0c18cafa-16af-48b3-b4d9-166a70e10a78)

---

### manual install

if you wish not to use `stow` and `install.sh`, you can find the config files for each program insie of its directory at the end of the file structure chain
(for example the config files for neovim are in `nvim/.config/nvim` because that's how stow works)

---

### notes

#### shells

the `.throwaway` file is a file for any code installed by other programs that pollutes your `.zshrc` or `.bashrc` and you want it out of there
