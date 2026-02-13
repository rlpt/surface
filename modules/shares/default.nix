{ pkgs, ... }:

{
  name = "shares";
  description = "Plain-text share allocation tracking (cap table)";
  packages = with pkgs; [ pandoc typst ];
  scripts = [
    (pkgs.writeShellScriptBin "shares" (builtins.readFile ./scripts/shares.sh))
  ];
  helpText = builtins.readFile ./scripts/help.txt;
}
