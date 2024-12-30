PATH="$PATH:$HOME/.bin:$HOME/.local/bin"
export PATH

EDITOR=nvim
export EDITOR

# share history with zsh
HISTFILE=$HOME/.histfile
HISTSIZE=1000
SAVEHIST=1000

dim="\[$(tput dim)\]"
reset="\[$(tput sgr0)\]"
green="\[$(tput setaf 2)\]"
PS1="$dim[$reset$green\u$reset$dim@$reset$green\h$reset \W$dim]\$$reset "

export GPG_TTY=$(tty)
