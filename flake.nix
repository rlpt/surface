{
  description = "Surface — formabi company-as-code root shell";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachSystem [ "x86_64-linux" "aarch64-darwin" ] (system:
      let
        pkgs = import nixpkgs { inherit system; };

        # --- People ---
        roster = import ./people;

        # --- Roles ---
        roles = import ./roles { inherit pkgs; };

        # All role packages merged (initially include everything;
        # role-scoping per user comes later)
        allRolePackages = builtins.concatLists
          (builtins.map (r: r.packages) (builtins.attrValues roles));

        # --- Modules (child directories, auto-discovered) ---
        modules = import ./modules { inherit pkgs; };

        modulePackages = builtins.concatLists
          (builtins.map (m: m.packages) modules);

        moduleNames = builtins.map (m: m.name) modules;
        moduleCount = builtins.length modules;

        # --- Roles JSON for scripts ---
        rolesJson = builtins.toJSON (builtins.mapAttrs (name: role: {
          inherit (role) description repos serverAccess context;
        }) roles);

        # --- Shell scripts ---
        halp = pkgs.writeShellScriptBin "halp" (builtins.readFile ./scripts/halp.sh);
        whoami-surface = pkgs.writeShellScriptBin "whoami" (builtins.readFile ./scripts/whoami.sh);
        onboard = pkgs.writeShellScriptBin "onboard" (builtins.readFile ./scripts/onboard.sh);

        # --- Base packages ---
        basePackages = [
          pkgs.git
          pkgs.jq
          halp
          whoami-surface
          onboard
        ];

        # Module listing for banner
        moduleListLines = builtins.concatStringsSep "\n"
          (builtins.map (m: "  - ${m.name}") modules);

      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = basePackages ++ allRolePackages ++ modulePackages;

          SURFACE_MODULES = builtins.concatStringsSep "," moduleNames;

          shellHook = ''
            # Set SURFACE_ROOT to the actual working directory (not nix store)
            export SURFACE_ROOT="$PWD"

            # Ensure our custom scripts shadow coreutils (whoami)
            export PATH="${whoami-surface}/bin:$PATH"

            # Write roles.json for scripts to read
            mkdir -p "$SURFACE_ROOT/roles"
            cat > "$SURFACE_ROOT/roles/roles.json" << 'ROLES_EOF'
            ${rolesJson}
            ROLES_EOF

            # Detect user
            GIT_EMAIL=$(git config user.email 2>/dev/null || echo "")
            USER_NAME=""
            if [ -n "$GIT_EMAIL" ] && [ -f "$SURFACE_ROOT/people/roster.json" ]; then
              USER_NAME=$(${pkgs.jq}/bin/jq -r --arg email "$GIT_EMAIL" \
                '.[] | select(.email == $email) | .name // empty' \
                "$SURFACE_ROOT/people/roster.json" 2>/dev/null || echo "")
            fi

            echo ""
            echo "surface shell"
            echo "============="
            if [ -n "$USER_NAME" ]; then
              echo "Welcome, $USER_NAME"
            else
              echo "User: unidentified — run 'onboard' to get started"
            fi
            echo ""
            echo "Modules: ${toString moduleCount}"
            echo "${moduleListLines}"
            echo ""
            echo "Commands: halp | whoami | onboard"
            echo ""
          '';
        };
      }
    );
}
