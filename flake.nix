{
  description = "Harlan A Nelson - Quarto website development environment";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
          config.allowUnfreePredicate = pkg:
            builtins.elem (pkgs.lib.getName pkg) [
              "claude-code"
            ];
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
            pkgs.claude-code
            pkgs.netlify-cli
          ];

          shellHook = ''
            echo "HarlanANelson website dev environment"
            echo "  R:       $(R --version | head -1)"
            echo "  Quarto:  $(quarto --version)"
            echo "  Claude:  $(claude --version 2>/dev/null || echo 'available')"
            echo "  Netlify: $(netlify --version 2>/dev/null | head -1 || echo 'available')"
          '';
        };
      }
    );
}
