HISTSIZE=10000
SAVEHIST=1000
setopt SHARE_HISTORY

unsetopt beep

# ------------------------------
#        Plugins & Config
# ------------------------------

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
export MANPAGER="nvim +Man!"
export PATH="$PATH:$HOME/.bin:$HOME/.local/bin"
# check if go installed and add its bin to path
if command -v go >/dev/null 2>&1; then
  export PATH="$PATH:$(go env GOPATH)/bin"
fi
export GPG_TTY="$(tty)"

# GCR handles desktop shells; remote shells need a session-local agent.
if [[ -n ${SSH_CONNECTION:-} ]]; then
  source "$HOME/.config/shells/.ssh-agentrc"
fi

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

autoload -Uz vcs_info
zstyle ':vcs_info:git:*' formats '%b'
zstyle ':vcs_info:*' enable git

function git_status() {
  GIT_OPTIONAL_LOCKS=0 \
  git status --porcelain=v1 -b --ignore-submodules=dirty 2>/dev/null | awk '
    NR==1 {
      sub(/^## /,"")
      if ($0 ~ /^No commits yet on /) {
        sub(/^No commits yet on /,"")
      }
      sub(/\.\.\..*/,"")
      branch=$0
      next
    }
    substr($0,1,2) == "??" { untracked++; next }
    substr($0,1,1) != " " { staged++ }
    substr($0,2,1) != " " { unstaged++ }
    END {
      if (branch != "")
        printf "%s %d %d %d", branch, staged+0, unstaged+0, untracked+0
    }
  '
}

setopt prompt_subst
setopt transient_rprompt

function prompt() {
  local LAST_EXIT_CODE=$?
  local USER_HOST="${USER}@${HOST%%.*}"

  RPROMPT="${dim}${USER_HOST}${reset}"
  [[ $LAST_EXIT_CODE -ne 0 ]] && RPROMPT="$RPROMPT ${red}${LAST_EXIT_CODE}${reset}"

  local gi gb staged unstaged untracked
  gi=$(git_status)

  if [[ -n $gi ]]; then
    read -r gb staged unstaged untracked <<< "$gi"
    local BRANCH_FORMAT=" ${dim}${gb}${reset}"

    (( unstaged > 0 ))  && RPROMPT="${yellow}${unstaged}*${reset} $RPROMPT"
    (( staged > 0 ))    && RPROMPT="${green}${staged}+${reset} $RPROMPT"
    (( untracked > 0 )) && RPROMPT="${red}${untracked}?${reset} $RPROMPT"
  else
    local BRANCH_FORMAT=""
  fi

  local ENV_FORMAT=""
  [[ -v DISTROBOX_ENTER_PATH ]] && ENV_FORMAT+="(distrobox) "
  [[ -v VIRTUAL_ENV ]] && ENV_FORMAT+="(venv) "
  [[ -v SSH_CONNECTION ]] && ENV_FORMAT+="(ssh) "

  local EXIT_CODE_COLOR=$green
  [[ $LAST_EXIT_CODE -ne 0 ]] && EXIT_CODE_COLOR=$red

  local IS_ROOT=0
  [[ $EUID -eq 0 ]] && IS_ROOT=1
  [[ $IS_ROOT -eq 1 ]] && ENV_FORMAT+="${yellow}󰨐${reset} "

  PROMPT="${dim}${ENV_FORMAT}${reset}${cyan}%1~${reset}${BRANCH_FORMAT} ${bold}${EXIT_CODE_COLOR}❭ ${reset}"
}

precmd_functions+=(prompt)

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
# vim: ft=bash
