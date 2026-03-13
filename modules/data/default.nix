{ pkgs, ... }:

{
  name = "data";
  description = "Company data (TOML files in data/)";
  packages = with pkgs; [ dolt ];  # dolt kept available for future use
  scripts = [
    (pkgs.writeShellScriptBin "data" (builtins.readFile ./scripts/data.sh))
  ];
  helpText = builtins.readFile ./scripts/help.txt;
}
