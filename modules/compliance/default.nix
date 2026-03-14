{ pkgs, ... }:

{
  name = "compliance";
  description = "Statutory compliance calendar and deadline tracking";
  packages = [ pkgs.python3 pkgs.pandoc pkgs.typst ];
  scripts = [
    (pkgs.writeShellScriptBin "compliance" ''
      exec python3 "$SURFACE_ROOT/modules/compliance/scripts/compliance.py" "$@"
    '')
  ];
  helpText = builtins.readFile ./scripts/help.txt;
}
