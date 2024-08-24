HISTSIZE=10000
SAVEHIST=1000
setopt SHARE_HISTORY

unsetopt beep

zstyle :compinstall filename "$HOME/.config/shells/.zshrc"

autoload -Uz compinit
compinit

zstyle ":completion:*" menu select

# ------------------------------
#           Variables
# ------------------------------

export EDITOR="nvim"
export PATH="$PATH:$HOME/.bin:$HOME/.local/bin"
export GPG_TTY="$(tty)"

# ------------------------------
#            Prompt
# ------------------------------

dim="%{$(tput dim)%}"
bold="%{$(tput bold)%}"

reset="%{$(tput sgr0)%}"

red="%{$(tput setaf 1)%}"
green="%{$(tput setaf 2)%}"
yellow="%{$(tput setaf 3)%}"
blue="%{$(tput setaf 4)%}"
magenta="%{$(tput setaf 5)%}"
cyan="%{$(tput setaf 6)%}"
white="%{$(tput setaf 7)%}"

function git_branch() {
  branch=$(git symbolic-ref HEAD 2> /dev/null | awk 'BEGIN{FS="/"} {print $NF}')
  if [[ $branch == "" ]];
  then
    :
  else
    echo " ${dim}${branch}${reset}"
  fi
}

# default bash prompt with colours and a % instead of a $
#PROMPT="${dim}[${reset}${green}%n${reset}${dim}@${reset}${green}%m${reset} %1~${dim}]%%${reset} "
# minimal prompt
setopt prompt_subst
prompt () {
  PS1="${cyan}%1~${reset}$(git_branch) ${bold}${red}⟩ ${reset}"
}
precmd_functions+=(prompt)

# ------------------------------
#           Plugins
# ------------------------------

plug "zap-zsh/supercharge"
plug "zsh-users/zsh-autosuggestions"

plug "zsh-users/zsh-syntax-highlighting"

# ------------------------------
#          Shell stuff
# ------------------------------

# cool update title so it can be hijacked by the WM to change decoration name

function update_title() {
  local user_host="${USER}@${HOST%%.*}"
  local current_dir
  if [ "$PWD" = "$HOME" ]; then
    current_dir="~"
  else
    current_dir="${PWD:t}"
  fi
  echo -ne "\033]0;${user_host}:${current_dir} - zsh\007"
}

precmd_functions+=("update_title")

# vi mode and related

bindkey -v
bindkey "^H" backward-delete-char
bindkey "^?" backward-delete-char
export KEYTIMEOUT=1

function zle-keymap-select {
  if [[ ${KEYMAP} == vicmd ]] ||
     [[ $1 = 'block' ]]; then
    echo -ne '\e[1 q'
  elif [[ ${KEYMAP} == main ]] ||
       [[ ${KEYMAP} == viins ]] ||
       [[ ${KEYMAP} = '' ]] ||
       [[ $1 = 'beam' ]]; then
    echo -ne '\e[5 q'
  fi
}
zle -N zle-keymap-select
zle-line-init() {
    zle -K viins
    echo -ne "\e[5 q"
}
zle -N zle-line-init
echo -ne '\e[5 q'
preexec() { echo -ne "\e[5 q" ;}

zle -A kill-whole-line vi-kill-line
zle -A backward-kill-word vi-backward-kill-word
zle -A backward-delete-char vi-backward-delete-char
