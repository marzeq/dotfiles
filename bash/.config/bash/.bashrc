PATH="$PATH:$HOME/.bin"

export PATH
PS1="\[\e[2m\][\[\e[0;92m\]\u\[\e[0;2m\]@\[\e[0;92m\]\h\[\e[0m\] \W\[\e[2m\]]\\$\[\e[0m\] "

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

if command -v gpg &> /dev/null; then
  export GPG_TTY=$(tty)
  # force gpg to use TUI password input
  gpg-connect-agent updatestartuptty /bye >/dev/null
fi
