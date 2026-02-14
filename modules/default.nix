{ pkgs, surface }:

let
  contents = builtins.readDir ./.;

  # Only include directories that contain a default.nix
  dirNames = builtins.filter
    (name:
      contents.${name} == "directory"
      && builtins.pathExists (./. + "/${name}/default.nix"))
    (builtins.attrNames contents);

  # Extend surface so modules can reference each other (lazy — no strict cycle)
  surface' = surface // { modules = modulesByName; };

  # Apply defaults and merge scripts into packages
  normalize = dirName: raw:
    let
      name = raw.name or (throw "Module '${dirName}' is missing required 'name' attribute");
      defaults = {
        inherit name;
        description = "";
        packages = [];
        helpText = "";
        shellHook = "";
        enabled = true;
      };
      merged = defaults // raw;
      scripts = raw.scripts or [];
    in
      builtins.removeAttrs (merged // {
        packages = merged.packages ++ scripts;
      }) [ "scripts" ];

  enabledModules = builtins.filter (m: m.enabled)
    (builtins.map
      (dirName: normalize dirName (import (./. + "/${dirName}") { pkgs = pkgs; surface = surface'; }))
      dirNames);

  modulesByName = builtins.listToAttrs
    (builtins.map (m: { name = m.name; value = m; }) enabledModules);

in
enabledModules
