{
  description = "terminal-width: a Claude Code mod that tells the model the terminal's width";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-parts.url = "github:hercules-ci/flake-parts";
    systems.url = "github:nix-systems/default";
    # The builder library, not a skill: its `devshellSkills` module gives
    # numtide/devshell with the menu, the skills startup and the standard
    # commands. The skills live in the `skills-devshell/` sub-flake, run on
    # entry, so this flake carries no skill inputs.
    agent-skill-flake = {
      url = "github:nhooey/agent-skill-flake";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    treefmt-nix = {
      url = "github:numtide/treefmt-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs =
    { flake-parts, systems, ... }@inputs:
    flake-parts.lib.mkFlake { inherit inputs; } {
      systems = import systems;
      imports = [
        # numtide/devshell, a motd pointing at `menu`, the startup that
        # installs skills-devshell/'s skills into .agents/skills/, and the
        # `check`, `fmt`, `update-flake` and skills commands.
        inputs.agent-skill-flake.flakeModules.devshellSkills
        # Sets `formatter` to treefmt and adds a `checks.treefmt` that fails
        # `nix flake check` on unformatted files.
        inputs.treefmt-nix.flakeModule
      ];
      agent-skill-flake.devshellSkills.name = "terminal-width";
      perSystem =
        { pkgs, ... }:
        let
          # The repository's one command-line tool; `mod --help` lists its
          # commands. claude itself is unfree and changes daily, so it comes
          # from PATH.
          mod = pkgs.writeShellApplication {
            name = "mod";
            runtimeInputs = [
              pkgs.python3
              pkgs.typescript
            ];
            text = ''exec python3 ${./scripts/mod.py} "$@"'';
          };
        in
        {
          packages.mod = mod;
          checks.mod-tests = pkgs.runCommand "mod-tests" { nativeBuildInputs = [ pkgs.python3 ]; } ''
            PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s ${./scripts} -p 'test_*.py'
            touch "$out"
          '';
          devshells.default = {
            # For editors; mod brings its own tsc.
            packages = [ pkgs.typescript ];
            # Concatenated onto the module's commands in `menu`.
            commands = [
              # dev
              {
                category = "dev";
                package = mod;
                help = "Validate, test and type-check the mod; mod --help lists its commands";
              }
            ];
          };
          treefmt = {
            projectRootFile = "flake.nix";
            programs.nixfmt.enable = true;
          };
        };
    };
}
