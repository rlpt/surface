{ pkgs, ... }:

{
  name = "shares";
  description = "Share allocation tracking — cap table";
  packages = with pkgs; [
    pandoc
    typst
    (python3.withPackages (ps: with ps; [
      openpyxl
    ]))
  ];
  scripts = [
    (pkgs.writeShellScriptBin "shares" ''
      exec python3 "$SURFACE_ROOT/modules/shares/scripts/shares.py" "$@"
    '')
  ];
  helpText = builtins.readFile ./scripts/help.txt;
}
