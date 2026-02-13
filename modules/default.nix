{ pkgs, surface }:

let
  contents = builtins.readDir ./.;
  dirNames = builtins.filter
    (name: contents.${name} == "directory")
    (builtins.attrNames contents);
in
builtins.map (name: import (./. + "/${name}") { inherit pkgs surface; }) dirNames
