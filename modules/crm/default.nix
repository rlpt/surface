{ pkgs, ... }:

{
  name = "crm";
  description = "CRM — contacts, deals, pipeline (dolt)";
  packages = [ pkgs.python3 ];
  scripts = [
    (pkgs.writeShellScriptBin "crm" ''
      exec python3 "$SURFACE_ROOT/modules/crm/scripts/crm.py" "$@"
    '')
  ];
  helpText = builtins.readFile ./scripts/help.txt;
}
