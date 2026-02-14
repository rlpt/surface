{ pkgs, ... }:

{
  name = "image-upload";
  description = "Upload images from your phone via QR code (uses upload.zolanic.space)";
  packages = with pkgs; [ curl jq qrencode ];
  scripts = [
    (pkgs.writeShellScriptBin "image-upload" (builtins.readFile ./scripts/image-upload.sh))
  ];
  helpText = builtins.readFile ./scripts/help.txt;
}
