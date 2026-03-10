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
    (pkgs.writeShellScriptBin "shares" ''
      exec python3 "$SURFACE_ROOT/modules/shares/scripts/shares.py" "$@"
    '')
  ];
  helpText = builtins.readFile ./scripts/help.txt;
}
