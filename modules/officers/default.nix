{ pkgs, ... }:

{
  name = "officers";
  description = "Company officers register (directors, secretary, PSC)";
  packages = [ pkgs.python3 pkgs.pandoc pkgs.typst ];
  scripts = [
    (pkgs.writeShellScriptBin "officers" ''
      exec python3 "$SURFACE_ROOT/modules/officers/scripts/officers.py" "$@"
    '')
  ];
  helpText = builtins.readFile ./scripts/help.txt;
}
