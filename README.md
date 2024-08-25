# dotfiles

this is for my own usage, but feel free to use any of this if you want

### install 

the repo utilises `GNU stow`. make sure you install the [stow package](https://archlinux.org/packages/extra/any/stow/) and then do these commands if you want to install it on your own machine:

```bash
cd dotfiles # or wherever you cloned the repository
stow <program_name_1> <program_name_2> # ...
# for example: stow nvim/ alacritty/
```

---
 
### gallery

#### neovim

![image](https://github.com/user-attachments/assets/ae1c454a-9351-4f3e-9228-a4f8d15b94af)

![image](https://github.com/user-attachments/assets/0c18cafa-16af-48b3-b4d9-166a70e10a78)

#### hyprland desktop

![image](https://github.com/marzeq/dotfiles/assets/58303665/c5cd3581-6143-4bfa-8266-6a98d3c6959e)

---

### automatic install script

run the `install.sh` script to stow the config files for the specified package of programs and install the necessary dependencies:

```bash
./install.sh [package]
# available packages: shells, neovim, alacritty, hyprland
```

---

### manual install

if you wish not to use `stow` and `install.sh`, you can find the config files for each program insie of its directory at the end of the file structure chain
(for example the config files for neovim are in `nvim/.config/nvim` because that's where they should reside in)

---

### notes

#### bash

the `.throwaway` file is a file for any scripts installed by other programs (for example `rustup`) that just pollute your `.bashrc` needlesly
