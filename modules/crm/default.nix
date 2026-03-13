{ pkgs, ... }:

{
  name = "crm";
  description = "CRM — customer contract management (dolt)";
  packages = [ pkgs.python3 pkgs.pandoc pkgs.typst ];
  scripts = [
    (pkgs.writeShellScriptBin "crm" ''
      exec python3 "$SURFACE_ROOT/modules/crm/scripts/crm.py" "$@"
    '')
  ];
  helpText = builtins.readFile ./scripts/help.txt;
}
