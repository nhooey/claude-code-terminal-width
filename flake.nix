{
  description = "terminal-width: a Claude Code mod that tells the model the terminal's width";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-parts.url = "github:hercules-ci/flake-parts";
    systems.url = "github:nix-systems/default";
  };

  outputs =
    { flake-parts, systems, ... }@inputs:
    flake-parts.lib.mkFlake { inherit inputs; } {
      systems = import systems;
      perSystem =
        { pkgs, ... }:
        let
          # claude itself is unfree and changes daily, so it comes from PATH.
          check = pkgs.writeShellApplication {
            name = "check";
            runtimeInputs = [ pkgs.typescript ];
            text = builtins.readFile ./scripts/check.sh;
          };
        in
        {
          apps.check = {
            type = "app";
            program = "${check}/bin/check";
          };
          devShells.default = pkgs.mkShell {
            packages = [
              pkgs.typescript
              check
            ];
          };
          formatter = pkgs.nixfmt;
        };
    };
}
