#!/bin/bash

# switch between root and normal user with the command 'op'
# 'op' stands for 'operator'
function op()
{
	if [ "`id -u`" = 0 ]; then
		exit
	else
		sudo su -
	fi
}

unalias -a

alias search='sudo dnf search'
alias get='sudo dnf install'

alias mkdir='mkdir -p'

alias h='history'
alias j='jobs -l'
alias path='echo -e ${PATH//:/\\n}'
alias libpath='echo -e ${LD_LIBRARY_PATH//:/\\n}'

alias du='du -kh'
alias df='df -kTh'

alias vim="$EDITOR"
alias v="$EDITOR"
alias vi="$EDITOR"
alias e="emacs -nw"
alias imv=imv-wayland

if [ "$(type -t _completion_loader 2>/dev/null)" = function ]; then
	_completion_loader task
	alias t=task
	complete -F _task t
fi

alias ug='ug -I'

alias grep='grep --color=auto'
alias gg='git grep --untracked'
alias grin='grep -rin --exclude-dir=build'

alias gito='git log --oneline'
alias gs='git status'

alias gitdifftree='git diff-tree --no-commit-id --name-only -r'

if dircolors &>/dev/null; then
	eval $(dircolors ~/.dir_colors)
elif uname -s | grep -qE 'Darwin|FreeBSD'; then
	export CLICOLOR=1
	export LSCOLORS=ExgxfxdxCxegedabagacad
fi
lsopt="-hF"
if command ls --time-style=iso &>/dev/null; then
	lsopt="$lsopt --time-style=iso"
fi
if command ls --color=auto &>/dev/null; then
	lsopt="$lsopt --color=auto"
fi
alias ls="ls $lsopt"
unset lsopt
alias la="ls -A"
alias ll="ls -l"
alias l="ls -l"
alias lla="ls -lA"

alias pg='pgrep -a'

alias ldapsearch='ldapsearch -Q -o ldif-wrap=no -LLL'

if command ip -h 2>&1 | grep -qF -- '-c[olor]'; then
	alias ip="ip -color=auto"
fi
bridge_opts=
if command bridge -h 2>&1 | grep -qF -- '-color'; then
	bridge_opts="-color=auto"
fi
if command bridge -h 2>&1 | grep -qF -- '-c[ompressvlans]'; then
	bridge_opts="$bridge_opts -compressvlans"
fi
if [ -n "$bridge_opts" ]; then
	alias bridge="bridge $bridge_opts"
fi
unset bridge_opts

function env() {
	if [ $# -eq 0 ]; then
		command env | sort
	else
		command env "$@"
	fi
}

alias sshunsafe='ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null'
alias scpunsafe='scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null'

# fuzzy find (case insensitive)
function ff() {
	local pattern="$1"
	shift
	if [ $# -eq 0 ]; then
		set -- . -printf '%P\n'
	fi
	find "$@" | grep -i -- "$pattern"
}

alias diff='diff -up'

if type pinfo >/dev/null 2>&1; then
	alias info=pinfo
fi

alias ncal='ncal -Mw3'

function termcolors() {
	local i
	for i in {0..255}; do
		printf "\e[38;5;%sm%3d\e[0m \e[1;38;5;%sm%3d\e[0m \e[48;5;%sm%3d\e[0m " \
			"$i" "$i" "$i" "$i" "$i" "$i"
		if (( i == 7 )) || (( i == 15 )); then
			printf '\n'
		elif (( i > 15 )) && (( (i-15) % 6 == 0 )); then
			printf '\n'
		fi
	done
}

function termcolor() {
	local rgb i
	stty -echo
	for i in "$@"; do
		if ! [ "$i" -ge 0 ] || ! [ "$i" -lt 256 ]; then
			echo "error: invalid color index: $i"
			continue
		fi
		printf "\e]4;$i;?\e\\"
		read -r -d "\\" x < /dev/tty
		rgb=$(printf '%s\n' "$x" | sed -nre 's,.*;rgb:([a-f0-9][a-f0-9])[a-f0-9][a-f0-9]/([a-f0-9][a-f0-9])[a-f0-9][a-f0-9]/([a-f0-9][a-f0-9])[a-f0-9][a-f0-9].*,\1\2\3,p')
		printf "\e[38;5;%sm%3d\e[0m \e[48;5;%sm%3d\e[0m \e[38;5;%sm#%s\e[0m \e[48;5;%sm#%s\e[0m\n" \
			"$i" "$i" "$i" "$i" "$i" "$rgb" "$i" "$rgb"
	done
	stty echo
}

function termcolors_text() {
	local text=$1
	shift
	for i in "$@"; do
		printf "\e[38;5;%sm%s -> %s\e[0m\n" "$i" "$text" "$i"
	done
}
