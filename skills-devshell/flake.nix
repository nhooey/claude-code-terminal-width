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

    # Every input below this divider is a skill source. Each follows
    # `nixpkgs` but not `agent-skill-flake`, so it keeps its own compatible
    # builder.

    coding-agent-skills = {
      url = "github:nhooey/coding-agent-skills/overnight-skills";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    document-skills = {
      url = "github:nhooey/document-skills/overnight-skills";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    git-skills = {
      url = "github:nhooey/git-skills/overnight-skills";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    nix-skills = {
      url = "github:nhooey/nix-skills/overnight-skills";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    shell-skills = {
      url = "github:nhooey/shell-skills/overnight-skills";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    writing-skills = {
      url = "github:nhooey/writing-skills/overnight-skills";
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
        # Running a prompt as a headless session, keeping the scratchpad
        # tidy, and the cross-repository plan's graph.
        {
          source = inputs.coding-agent-skills;
          skills = [
            "coding-agent-headless-in-checkout"
            "coding-agent-plans-as-graph"
            "coding-agent-scratchpad-scripts"
          ];
        }
        # Markdown hygiene, for the README.
        { source = inputs.document-skills; }
        # Commits, branches and pull requests.
        { source = inputs.git-skills; }
        # Writing and bumping this flake.
        {
          source = inputs.nix-skills;
          skills = [
            "nix-flakes"
            "nix-flake-recursive-bump-input-versions"
          ];
        }
        # Safe shell commands: named deletes, PIDs, no machine-wide changes.
        { source = inputs.shell-skills; }
        # Prose hygiene, for the README and commit messages.
        { source = inputs.writing-skills; }
      ];
    };
}
