# dotfiles

this is for my own usage, but feel free to use any of this if you want

### install 

the repo utilises `GNU stow`. make sure you install the [stow package](https://archlinux.org/packages/extra/any/stow/) and then do these commands if you want to install it on your own machine:

```bash
cd dotfiles # or wherever you cloned the repository
stow <program_name_1> <program_name_2> # ...
# for example: stow nvim alacritty
```

### manual install

if you wish not to use `stow`, you can find the config files for each program insie of its directory at the end of the file structure chain
(for example the config files for neovim are in `nvim/.config/nvim` because that's where they should reside in)

### notes

#### bash

the `.throwaway` file is a file for any scripts installed by other programs (for example `rustup`) that just pollute your `.bashrc` needlesly
