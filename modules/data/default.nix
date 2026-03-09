{ pkgs, ... }:

{
  name = "data";
  description = "Version-controlled database (dolt)";
  packages = with pkgs; [ dolt ];
  scripts = [
    (pkgs.writeShellScriptBin "data" (builtins.readFile ./scripts/data.sh))
  ];
  helpText = builtins.readFile ./scripts/help.txt;

  shellHook = ''
    export SURFACE_DB="$SURFACE_ROOT/.surface-db"
    if [ ! -d "$SURFACE_DB/.dolt" ]; then
      mkdir -p "$SURFACE_DB"
      (
        cd "$SURFACE_DB"
        dolt init --name "surface" --email "system@formabi.com"
        dolt sql < "$SURFACE_ROOT/modules/data/schema.sql"
        dolt sql < "$SURFACE_ROOT/modules/data/seed.sql"
        dolt add .
        dolt commit -m "init: schema and seed data"
      ) > /dev/null 2>&1
    fi
  '';
}
