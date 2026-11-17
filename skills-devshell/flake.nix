{
  description = "terminal-width dev-shell skill set: an isolated sub-flake the root dev shell runs on entry, never a root input, so the skill sources live only in this flake's lock.";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    systems.url = "github:nix-systems/default";

    # The builder library, not a skill: it provides `mkDevshellSkillsFlake`.
    agent-skill-flake = {
      url = "github:nhooey/agent-skill-flake";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    # The one skill source: skillspkgs' per-family combinations. It follows
    # `nixpkgs` but not `agent-skill-flake`, so it keeps its own compatible
    # builder.
    skillspkgs-combinations = {
      url = "github:nhooey/skillspkgs?dir=sources/combinations";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs =
    {
      nixpkgs,
      agent-skill-flake,
      ...
    }@inputs:
    agent-skill-flake.lib.mkDevshellSkillsFlake {
      inherit nixpkgs;
      systems = import inputs.systems;
      name = "terminal-width-devshell";
      sources = [
        # This repository is in the Claude Code tools family: the shared
        # base, shipped defaults, changelogs and strict TypeScript. No
        # additions: the family covers this TypeScript mod.
        { source = inputs.skillspkgs-combinations.combinations.claude-code-tools; }
      ];
    };
}
