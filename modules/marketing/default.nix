{ pkgs, ... }:

{
  name = "marketing";
  description = "Pitch decks, handbook, diagrams, and investor documents (Marp + Pandoc)";
  packages = with pkgs; [ marp-cli mermaid-cli pandoc ];
  scripts = [
    (pkgs.writeShellScriptBin "marketing" (builtins.readFile ./scripts/marketing.sh))
  ];
  helpText = builtins.readFile ./scripts/help.txt;
}
