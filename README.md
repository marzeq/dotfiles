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

**fyi - this script was made for my personal use and you should probably not run it yourself**

run the `install.sh` script to stow the config files for the specified package of programs and install the necessary dependencies:

```bash
./install.sh [package]
```

---
 
### gallery

#### hyprland desktop

![2025-10-01-190047_hyprshot](https://github.com/user-attachments/assets/0873d07e-ea08-4094-a696-3c02b77518dc)
![2025-10-01-190025_hyprshot](https://github.com/user-attachments/assets/2a0b27bf-58ec-408c-9f72-d5fc71c9cece)
![2025-10-01-190115_hyprshot](https://github.com/user-attachments/assets/dde1e5d6-5e80-4868-855c-59847d58021d)
![2025-10-01-190102_hyprshot](https://github.com/user-attachments/assets/2eeabe81-f6d4-4a60-b95f-d8fe64613be0)

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
