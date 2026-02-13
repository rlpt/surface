{ pkgs, ... }:

{
  name = "hello";
  description = "Sample child module";
  packages = with pkgs; [ hello ];
  enabled = false;
}
