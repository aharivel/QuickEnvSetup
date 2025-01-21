.PHONY: install
install: dotfiles scripts
  @:

DOTFILES += bash_aliases
DOTFILES += bash_profile
DOTFILES += bashrc
DOTFILES += colordiffrc
DOTFILES += dir_colors
DOTFILES += tmate.conf
DOTFILES += tmux.conf

.PHONY: dotfiles
dotfiles: $(addprefix $(HOME)/.,$(DOTFILES))
	@:

$(HOME)/.%: %
	@! [ -e $@ ] || rm -rf -- $@
	@mkdir -pv $(@D)
	@ln -srv $< $@

BINFILES = $(wildcard bin/*)

.PHONY: scripts
scripts: $(addprefix $(HOME)/,$(BINFILES))
	@:

$(HOME)/bin/%: bin/%
	@! [ -e $@ ] || rm -rf -- $@
	@mkdir -pv $(@D)
	@ln -srvf $< $@
