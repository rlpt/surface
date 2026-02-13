{ pkgs, ... }:

{
  name = "accounts";
  description = "Plain-text bookkeeping (hledger)";
  packages = with pkgs; [ hledger ];
  scripts = [
    (pkgs.writeShellScriptBin "accounts" (builtins.readFile ./scripts/accounts.sh))
  ];
  helpText = builtins.readFile ./scripts/help.txt;
}
