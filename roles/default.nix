{ pkgs }:

{
  engineering = {
    description = "Application development — Elm frontend, Rust/Node backend";
    repos = [ "formabi-app" "latice" ];
    packages = with pkgs; [ elmPackages.elm nodejs cargo rustc ];
    serverAccess = "none";
    context = [ "app" ];
  };

  ops = {
    description = "Infrastructure, deployment, and server management";
    repos = [ "cmdr" ];
    packages = with pkgs; [ deploy-rs age ssh-to-age ];
    serverAccess = "wheel";
    context = [ "ops" ];
  };

  sales = {
    description = "Decks, demos, and customer-facing materials";
    repos = [ "deck" ];
    packages = with pkgs; [ marp-cli ];
    serverAccess = "none";
    context = [ "sales" ];
  };

  design = {
    description = "Design system and visual identity";
    repos = [ "zolanic" ];
    packages = with pkgs; [ nodejs ];
    serverAccess = "none";
    context = [ "design" ];
  };
}
