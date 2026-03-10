{ pkgs, ... }:

{
  name = "shares";
  description = "Share allocation tracking — cap table (dolt)";
  packages = with pkgs; [
    pandoc
    typst
    (python3.withPackages (ps: with ps; [
      google-api-python-client
      google-auth-oauthlib
    ]))
  ];
  scripts = [
    (pkgs.writeShellScriptBin "shares" (builtins.readFile ./scripts/shares.sh))
  ];
  helpText = builtins.readFile ./scripts/help.txt;
}
