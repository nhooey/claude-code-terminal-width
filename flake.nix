{
  description = "terminal-width: a Claude Code mod that tells the model the terminal's width";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-parts.url = "github:hercules-ci/flake-parts";
    systems.url = "github:nix-systems/default";
    # The builder library, not a skill: its `devshellSkillsHook` gives the
    # dev shell's startup line. The skills live in the `skills-devshell/`
    # sub-flake, run on entry, so this flake carries no skill inputs.
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
      # Sets `formatter` to treefmt and adds a `checks.treefmt` that fails
      # `nix flake check` on unformatted files.
      imports = [ inputs.treefmt-nix.flakeModule ];
      perSystem =
        { pkgs, ... }:
        let
          devshellSkills = inputs.agent-skill-flake.lib.devshellSkillsHook { };
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
          devShells.default = pkgs.mkShell {
            packages = [
              pkgs.typescript
              mod
            ];
            # Install, update and sweep skills-devshell/'s skills into
            # .agents/skills/. The hook expects numtide/devshell's $PRJ_ROOT.
            shellHook = ''
              PRJ_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
              export PRJ_ROOT
              ${devshellSkills.startup}
            '';
          };
          treefmt = {
            projectRootFile = "flake.nix";
            programs.nixfmt.enable = true;
          };
        };
    };
}
