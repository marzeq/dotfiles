PATH="$PATH:$HOME/.bin:$HOME/.local/bin"
export PATH

EDITOR=nvim
export EDITOR

HISTSIZE=1000
SAVEHIST=1000

PROMPT_TYPE="minimal"

prompt_minimal() {
  local LAST_EXIT_CODE=$?
  local RESET="\[\e[0m\]"
  local DIM="\[\e[2m\]"
  local BOLD="\[\e[1m\]"
  local RED="\[\e[31m\]"
  local GREEN="\[\e[32m\]"
  local YELLOW="\[\e[33m\]"
  local CYAN="\[\e[36m\]"

  local USER_HOST="${USER}@${HOSTNAME%%.*}"
  local TIME=$(date +'%X')
  local RPROMPT="${DIM}${TIME} (${USER_HOST})${RESET}"

  local EXIT_CODE_COLOR=""
  if [[ $LAST_EXIT_CODE -eq 0 ]]; then
    EXIT_CODE_COLOR="${GREEN}"
  else
    EXIT_CODE_COLOR="${RED}"
    RPROMPT="${RED}${LAST_EXIT_CODE}${RESET} ${RPROMPT}"
  fi

  local BRANCH_FORMAT=""
  local gb=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)
  if [[ -n $gb ]]; then
    BRANCH_FORMAT=" ${DIM}${gb}${RESET}"
    local unstaged_changes=$(git diff --name-only 2>/dev/null | wc -l)
    local staged_changes=$(git diff --cached --name-only 2>/dev/null | wc -l)
    local untracked_files=$(git ls-files --others --exclude-standard 2>/dev/null | wc -l)

    [[ $unstaged_changes -gt 0 ]] && RPROMPT="${YELLOW}${unstaged_changes}*${RESET} ${RPROMPT}"
    [[ $staged_changes -gt 0 ]] && RPROMPT="${GREEN}${staged_changes}+${RESET} ${RPROMPT}"
    [[ $untracked_files -gt 0 ]] && RPROMPT="${RED}${untracked_files}?${RESET} ${RPROMPT}"
  fi

  local ENV_FORMAT=""
  [[ -n "$DISTROBOX_ENTER_PATH" ]] && ENV_FORMAT+="(distrobox) "
  [[ -n "$VIRTUAL_ENV" ]] && ENV_FORMAT+="(venv) "
  [[ -n "$SSH_CONNECTION" ]] && ENV_FORMAT+="(ssh) "

  PS1="${DIM}${ENV_FORMAT}${RESET}${CYAN}\w${RESET}${BRANCH_FORMAT} ${BOLD}${EXIT_CODE_COLOR}❭ ${RESET}"
}

prompt_bash_like() {
  local RESET="\[\e[0m\]"
  local DIM="\[\e[2m\]"
  local GREEN="\[\e[32m\]"
  PS1="${DIM}[${RESET}${GREEN}\u${RESET}${DIM}@${RESET}${GREEN}\h${RESET} \w${DIM}]\$${RESET} "
}

if [[ $PROMPT_TYPE == "minimal" ]]; then
  PROMPT_COMMAND=prompt_minimal
elif [[ $PROMPT_TYPE == "bash_like" ]]; then
  prompt_bash_like
else
  echo -e "\e[31mInvalid prompt type \e[1m\"$PROMPT_TYPE\"\e[0m"
fi

export GPG_TTY=$(tty)
