# vi: ft=bash
HISTSIZE=10000
SAVEHIST=1000
setopt SHARE_HISTORY

unsetopt beep

# ------------------------------
#        Plugins & Config
# ------------------------------

if [ -f "${XDG_DATA_HOME:-$HOME/.local/share}/zap/zap.zsh" ]; then
  source "${XDG_DATA_HOME:-$HOME/.local/share}/zap/zap.zsh"
else
  zsh <(curl -s https://raw.githubusercontent.com/zap-zsh/zap/master/install.zsh) --branch release-v1 --keep
fi

plug "zap-zsh/supercharge"
plug "zsh-users/zsh-autosuggestions"
plug "zsh-users/zsh-syntax-highlighting"
autoload -U compinit; compinit
plug "Aloxaf/fzf-tab"
export FZF_DEFAULT_OPTS="--color=16"
zstyle ":fzf-tab:*" fzf-flags ${(Q)${(Z:nC:)FZF_DEFAULT_OPTS}}

zstyle :compinstall filename "$HOME/.config/shells/.zshrc"

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

function is_in_dot_git() {
  if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    result=$(git rev-parse --is-inside-work-tree)
    if [ "$result" = "false" ]; then
      return 0
    fi

    return 1
  fi

  return 1
}

function git_branch() {
  if is_in_dot_git; then
    return
  fi

  branch=$(git symbolic-ref HEAD 2> /dev/null | awk 'BEGIN{FS="/"} {print $NF}')
  if [[ $branch != "" ]]; then
    echo $branch
  fi
}

PROMPT_TYPE="minimal"

if [[ $PROMPT_TYPE == "minimal" ]];
then
  setopt prompt_subst
  setopt transient_rprompt
  prompt() {
    local LAST_EXIT_CODE=$?
    local EXIT_CODE_COLOR
    local USER_HOST="${USER}@${HOST%%.*}"
    RPROMPT="${dim}$(date +'%X') (${USER_HOST})${reset}"
    if [[ $LAST_EXIT_CODE == 0 ]]; then
      EXIT_CODE_COLOR="${green}"
      RPROMPT="$RPROMPT"
    else
      EXIT_CODE_COLOR="${red}"
      RPROMPT="$RPROMPT ${red}${LAST_EXIT_CODE}${reset}"
    fi

    local BRANCH_FORMAT
    local gb=$(git_branch)
    if [[ $gb == "" ]];
    then
      BRANCH_FORMAT=""
    else
      BRANCH_FORMAT=" ${dim}${gb}${reset}"
      local unstaged_changes=$(git diff --name-only | wc -l)
      local staged_changes=$(git diff --cached --name-only | wc -l)
      local untracked_files=$(git ls-files --others --exclude-standard | wc -l)

      if [[ $unstaged_changes -gt 0 ]]; then
        RPROMPT="${yellow}${unstaged_changes}*${reset} $RPROMPT"
      fi

      if [[ $staged_changes -gt 0 ]]; then
        RPROMPT="${green}${staged_changes}+${reset} $RPROMPT"
      fi

      if [[ $untracked_files -gt 0 ]]; then
        RPROMPT="${red}${untracked_files}?${reset} $RPROMPT"
      fi
    fi

    local ENV_FORMAT=""
    if [[ -v DISTROBOX_ENTER_PATH ]]; then
      ENV_FORMAT+="(distrobox) "
    fi
    if [[ -v VIRTUAL_ENV ]]; then
      ENV_FORMAT+="(venv) "
    fi
    if [[ -v SSH_CONNECTION ]]; then
      ENV_FORMAT+="(ssh) "
    fi

    PROMPT="${dim}${ENV_FORMAT}${reset}${cyan}%1~${reset}${BRANCH_FORMAT} ${bold}${EXIT_CODE_COLOR}❭ ${reset}"
  }
  precmd_functions+=(prompt)
elif [[ $PROMPT_TYPE == "bash_like" ]];
then
  PROMPT="${dim}[${reset}${green}%n${reset}${dim}@${reset}${green}%m${reset} %1~${dim}]%%${reset} "
else
  echo "$(tput setaf 1)Invalid prompt type $(tput bold)\"$PROMPT_TYPE\"$(tput sgr0)"
fi

# ------------------------------
#          Shell stuff
# ------------------------------

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
