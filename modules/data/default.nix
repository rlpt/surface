{ pkgs, ... }:

{
  name = "data";
  description = "Company data (YAML files in data/)";
  packages = with pkgs; [ dolt python3Packages.pyyaml python3Packages.openpyxl ];
  scripts = [
    (pkgs.writeShellScriptBin "data" (builtins.readFile ./scripts/data.sh))
  ];
  helpText = builtins.readFile ./scripts/help.txt;
}
