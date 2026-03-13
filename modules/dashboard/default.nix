{ pkgs, surface, ... }:

let
  brandColors =
    if (surface.modules ? brand)
    then surface.modules.brand.identity.colors
    else { primary = "#6366f1"; accent = "#a78bfa"; bg = "#0a0a1a"; text = "#e0e0e0"; };
in
{
  name = "dashboard";
  description = "Read-only HTML dashboard of Dolt data";
  packages = [ pkgs.python3 ];
  scripts = [
    (pkgs.writeShellScriptBin "dashboard" ''
      export BRAND_PRIMARY="${brandColors.primary}"
      export BRAND_ACCENT="${brandColors.accent}"
      export BRAND_BG="${brandColors.bg}"
      export BRAND_TEXT="${brandColors.text}"
      exec python3 "$SURFACE_ROOT/modules/dashboard/scripts/dashboard.py" "$@"
    '')
  ];
  helpText = builtins.readFile ./scripts/help.txt;
}
