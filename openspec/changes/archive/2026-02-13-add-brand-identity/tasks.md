## 1. Logo Conversion

- [x] 1.1 Convert `/Users/rlpt/Downloads/formabi/formabi.eps` to SVG (Ghostscript/Inkscape)
- [x] 1.2 Inspect the SVG — verify vector paths and colours are preserved, no embedded raster
- [x] 1.3 Copy the clean SVG to `modules/brand/logo.svg`

## 2. Brand Module

- [x] 2.1 Create `modules/brand/default.nix` with `name`, `description`, `identity` attribute set (name, strapLine, colors, logoPath), and `helpText`
- [x] 2.2 Verify module auto-discovery — run `nix develop` and confirm `brand` appears in the shell banner

## 3. Verification

- [x] 3.1 Run `halp` and confirm a "Brand" section appears
- [x] 3.2 Commit the brand module and logo
