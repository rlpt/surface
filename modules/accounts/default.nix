{ pkgs, ... }:

{
  name = "accounts";
  description = "Double-entry bookkeeping (dolt)";
  packages = [ pkgs.python3 ];
  scripts = [
    (pkgs.writeShellScriptBin "accounts" ''
      exec python3 "$SURFACE_ROOT/modules/accounts/scripts/accounts.py" "$@"
    '')
  ];
  helpText = builtins.readFile ./scripts/help.txt;
}
