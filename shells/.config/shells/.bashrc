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

function update_title() {
  local user_host="${USER}@${HOSTNAME%%.*}"
  local current_dir
  if [ "$PWD" == "$HOME" ]; then
    current_dir="~"
  else
    current_dir=$(basename "$PWD")
  fi
  echo -ne "\033]0;${USER}@${HOSTNAME%%.*}:${current_dir} - bash\007"
}

export PROMPT_COMMAND="update_title"

export GPG_TTY=$(tty)
