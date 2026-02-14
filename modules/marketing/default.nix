{ pkgs, surface, ... }:

let
  # Cross-module reference with fallback — brand may not be present.
  # Uses surface.modules (lazy attrset of all sibling modules).
  brandIdentity =
    if (surface.modules ? brand)
    then surface.modules.brand.identity
    else {
      name = "Formabi";
      strapLine = "Complex Forms Made Easy";
      colors = { primary = "#6366f1"; accent = "#a78bfa"; bg = "#0a0a1a"; text = "#e0e0e0"; };
      logoPath = "modules/brand/logo.svg";
    };
in
{
  name = "marketing";
  description = "Pitch decks, handbook, diagrams, and investor documents (Marp + Pandoc)";
  packages = with pkgs; [ marp-cli mermaid-cli pandoc jq ];
  scripts = [
    (pkgs.writeShellScriptBin "marketing" (builtins.readFile ./scripts/marketing.sh))
  ];
  helpText = builtins.readFile ./scripts/help.txt;

  # Resolved brand identity — available to Nix consumers via modulesByName.marketing.brandIdentity
  inherit brandIdentity;
}
