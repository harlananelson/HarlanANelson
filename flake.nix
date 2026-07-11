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
