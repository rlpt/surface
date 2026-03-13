{ pkgs, ... }:

{
  name = "board";
  description = "Board meetings, minutes, and resolutions (dolt)";
  packages = [ pkgs.python3 pkgs.pandoc pkgs.typst ];
  scripts = [
    (pkgs.writeShellScriptBin "board" ''
      exec python3 "$SURFACE_ROOT/modules/board/scripts/board.py" "$@"
    '')
  ];
  helpText = builtins.readFile ./scripts/help.txt;
}
