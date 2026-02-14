{ pkgs, ... }:

{
  name = "brand";
  description = "Formabi brand identity — logo, colours, and strap line";
  packages = [];

  identity = {
    name = "Formabi";
    strapLine = "Complex Forms Made Easy";
    colors = {
      primary = "#6366f1";
      accent = "#a78bfa";
      bg = "#0a0a1a";
      text = "#e0e0e0";
    };
    logoPath = "modules/brand/logo.svg";
  };

  helpText = ''
    Brand identity data (logo, colours, strap line).
    Logo: modules/brand/logo.svg
    Access brand values via surface.modules.brand.identity in sibling modules.
  '';
}
