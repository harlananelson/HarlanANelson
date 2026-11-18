{
  description = "Harlan A Nelson - Quarto website development environment";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-26.05";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
        };

        rPackages = with pkgs.rPackages; [
          tidyverse
          tidymodels
          targets
          sparklyr
          rlang
          quarto
          knitr
          rmarkdown
          htmltools
          htmlwidgets
        ];

        rWithPackages = pkgs.rWrapper.override {
          packages = rPackages;
        };
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = [
            rWithPackages
            pkgs.quarto
            pkgs.pandoc
            pkgs.netlify-cli
            pkgs.tmux
          ];

          shellHook = ''
            # nix-name: give this shell a name when getpwuid has none for the uid.
            # On a host with no passwd entry for the uid, a pure nix shell otherwise
            # prompts "I have no name!". Where the name resolves, this block does nothing.
            # No LD_PRELOAD. The nixpkgs nss_wrapper is linked to a newer glibc than
            # the host, and preloading it breaks host binaries started from the shell.
            if ! id -un >/dev/null 2>&1; then
            _nn_dir="''${TMPDIR:-/tmp}/nix-name-$$"
            mkdir -p "$_nn_dir"
            _nn_name=$(logname 2>/dev/null || printf '%s' "''${USER:-nixuser}")
            printf '%s\n' '#!/bin/sh' "printf '%s\\n' '$_nn_name'" > "$_nn_dir/whoami"
            chmod +x "$_nn_dir/whoami"
            export PATH="$_nn_dir:''${PATH}"
            export USER="$_nn_name"
            export LOGNAME="$_nn_name"
            export PS1="$_nn_name@\h:\w\\$ "
            unset _nn_dir _nn_name
            fi
            echo "HarlanANelson website dev environment"
            echo "  R:       $(R --version | head -1)"
            echo "  Quarto:  $(quarto --version)"
            echo "  Claude:  $(claude --version 2>/dev/null || echo 'not found — install natively: https://claude.com/download') (system install, self-updating)"
            echo "  Netlify: $(netlify --version 2>/dev/null | head -1 || echo 'available')"
            echo "  tmux:    $(tmux -V 2>/dev/null || echo 'available')"
          '';
        };
      }
    );
}
