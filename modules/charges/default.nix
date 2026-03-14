{ pkgs, ... }:

{
  name = "charges";
  description = "Register of charges (secured loans and debentures)";
  packages = [ pkgs.python3 pkgs.pandoc pkgs.typst ];
  scripts = [
    (pkgs.writeShellScriptBin "charges" ''
      exec python3 "$SURFACE_ROOT/modules/charges/scripts/charges.py" "$@"
    '')
  ];
  helpText = builtins.readFile ./scripts/help.txt;
}
