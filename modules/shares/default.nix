{ pkgs, ... }:

{
  name = "shares";
  description = "Share allocation tracking — cap table (dolt)";
  packages = with pkgs; [ pandoc typst ];
  scripts = [
    (pkgs.writeShellScriptBin "shares" (builtins.readFile ./scripts/shares.sh))
  ];
  helpText = builtins.readFile ./scripts/help.txt;
}
