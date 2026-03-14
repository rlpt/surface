{ pkgs, ... }:

{
  name = "dividends";
  description = "Dividend declarations and payments";
  packages = [ pkgs.python3 pkgs.pandoc pkgs.typst ];
  scripts = [
    (pkgs.writeShellScriptBin "dividends" ''
      exec python3 "$SURFACE_ROOT/modules/dividends/scripts/dividends.py" "$@"
    '')
  ];
  helpText = builtins.readFile ./scripts/help.txt;
}
