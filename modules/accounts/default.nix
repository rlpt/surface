{ pkgs, ... }:

{
  name = "accounts";
  description = "Double-entry bookkeeping (dolt)";
  packages = [];
  scripts = [
    (pkgs.writeShellScriptBin "accounts" (builtins.readFile ./scripts/accounts.sh))
  ];
  helpText = builtins.readFile ./scripts/help.txt;
}
