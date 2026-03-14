{ pkgs, ... }:

{
  name = "company";
  description = "Company details register (name, number, address, SIC codes)";
  packages = [ pkgs.python3 pkgs.pandoc pkgs.typst ];
  scripts = [
    (pkgs.writeShellScriptBin "company" ''
      exec python3 "$SURFACE_ROOT/modules/company/scripts/company.py" "$@"
    '')
  ];
  helpText = builtins.readFile ./scripts/help.txt;
}
