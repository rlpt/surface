# Guild Server Plan

`guild.zolanic.space` — a single dedicated server where the founding team SSHs in, runs Claude Code, and shapes the company together.

## The Setup

Three people, one server:

| Person | Role | Technical level | What they do |
|--------|------|-----------------|--------------|
| Rich (rlpt) | engineering, ops | High | Builds product, manages infra, deploys |
| Louis | cofounder, business | Non-technical | Sales, discovery, strategy, brand, wears many hats |
| Mark | cofounder, business | Non-technical | Sales, discovery, operations, partnerships, wears many hats |

All three SSH into guild.zolanic.space. Each gets a home directory, Claude Code, and access to the company. Louis and Mark are generalists — they do sales, discovery, strategy, content, customer conversations, whatever's needed. They need access to everything except the technical internals (source code, server config).

Claude is the great equalizer — Louis and Mark don't need to know git commands or SQL because Claude handles that for them. They talk to Claude in plain English, Claude does the technical work.

## What's on the Guild Server

```
guild.zolanic.space
├── /home/rich/                     ← ops + engineering workspace
│   ├── .claude-context.md          ← full company context + ops + engineering
│   ├── repos/                      ← all repos (symlinked from /srv/repos/)
│   └── .ssh/authorized_keys
│
├── /home/louis/                    ← guild member workspace
│   ├── .claude-context.md          ← full company context (minus source code)
│   ├── repos/                      ← formabi, homepage, surface, latice (symlinked)
│   └── .ssh/authorized_keys
│
├── /home/mark/                     ← guild member workspace
│   ├── .claude-context.md          ← full company context (minus source code)
│   ├── repos/                      ← formabi, homepage, surface, latice (symlinked)
│   └── .ssh/authorized_keys
│
├── /srv/guild/                     ← shared company workspace
│   ├── formabi/                    ← the root repo (company-as-code)
│   │   ├── identity/
│   │   ├── brand/
│   │   ├── state/
│   │   ├── decisions/
│   │   ├── context/
│   │   └── ...
│   ├── ledger/                     ← Dolt database
│   └── repos/                      ← bare git repos (shared)
│       ├── formabi-app.git
│       ├── deck.git
│       ├── zolanic.git
│       └── cmdr.git
│
├── /srv/formabi/                   ← product instances (if colocated)
│
└── NixOS services
    ├── Dolt SQL server              ← guild ledger, always running
    ├── Forgejo                      ← git.zolanic.space (browser git)
    ├── Claude Code                  ← installed system-wide
    └── Tailscale                    ← VPN overlay
```

## NixOS Configuration

### Module Structure

```
deploy/servers/guild/
├── configuration.nix               ← guild-specific: hostname, firewall, secrets
└── hardware-configuration.nix      ← from nixos-generate-config

deploy/shared/                      ← reuse existing shared modules
├── common.nix                      ← tailscale, fail2ban, base packages (already exists)
├── guild-users.nix                 ← NEW: guild member accounts + permissions
├── guild-workspace.nix             ← NEW: shared workspace, repos, Dolt
├── guild-claude.nix                ← NEW: Claude Code setup per user
├── guild-guardrails.nix            ← NEW: safety nets for non-technical users
├── forgejo.nix                     ← reuse (maybe different domain)
└── ...
```

### guild-users.nix — Member Accounts

```nix
# deploy/shared/guild-users.nix
{ config, pkgs, lib, ... }:

let
  # Guild members — the single source of truth (until Dolt takes over)
  members = {
    rich = {
      name = "Rich";
      email = "rich@formabi.com";
      github = "rlpt";
      roles = [ "engineering" "ops" ];
      sshKeys = [ "ssh-ed25519 AAAA... rich@formabi.com" ];
      isAdmin = true;   # wheel group, sudo, full access
    };
    louis = {
      name = "Louis";
      email = "louis@formabi.com";
      github = "louisx";
      roles = [ "business" ];  # generalist — sees everything except source code + infra
      sshKeys = [ "ssh-ed25519 AAAA... louis@formabi.com" ];
      isAdmin = false;
    };
    mark = {
      name = "Mark";
      email = "mark@formabi.com";
      github = "markx";
      roles = [ "business" ];  # generalist — sees everything except source code + infra
      sshKeys = [ "ssh-ed25519 AAAA... mark@formabi.com" ];
      isAdmin = false;
    };
  };

  # Role → unix groups mapping
  roleGroups = {
    engineering = [ "engineering" "guild" ];
    ops = [ "ops" "guild" "wheel" ];
    business = [ "business" "guild" ];     # generalist business role
  };

  # Role → which repos they can see
  roleRepos = {
    engineering = [ "formabi" "formabi-app" "latice" "cmdr" ];
    ops = [ "formabi" "cmdr" ];
    business = [ "formabi" "homepage" "surface" "latice" ];  # everything except source code + infra
  };

  memberGroups = member:
    lib.unique (lib.concatMap (r: roleGroups.${r} or [ "guild" ]) member.roles);

  memberRepos = member:
    lib.unique (lib.concatMap (r: roleRepos.${r} or [ "formabi" ]) member.roles);

in {
  # Create groups
  users.groups = {
    guild = {};           # everyone
    engineering = {};
    ops = {};
    business = {};        # Louis and Mark — broad access, no admin
  };

  # Create users
  users.users = lib.mapAttrs (username: member: {
    isNormalUser = true;
    home = "/home/${username}";
    description = member.name;
    extraGroups = memberGroups member;
    openssh.authorizedKeys.keys = member.sshKeys;
    shell = pkgs.bash;
  }) members;

  # SSH config
  services.openssh = {
    enable = true;
    settings = {
      PasswordAuthentication = false;
      PermitRootLogin = "no";
      X11Forwarding = false;
    };
  };

  # Per-user home setup via activation scripts
  system.activationScripts.guildHomes = let
    setupUser = username: member: ''
      # Create repos directory and symlink allowed repos
      mkdir -p /home/${username}/repos
      chown ${username}:guild /home/${username}/repos

      # Remove stale symlinks
      find /home/${username}/repos -maxdepth 1 -type l -delete

      # Symlink repos for this member's roles
      ${lib.concatMapStringsSep "\n" (repo: ''
        if [ -d /srv/guild/repos/${repo}.git ]; then
          ln -sf /srv/guild/repos/${repo}.git /home/${username}/repos/${repo}
        fi
      '') (memberRepos member)}

      # Write claude context (assembled per role)
      cat > /home/${username}/.claude-context.md << 'CONTEXT'
      ${builtins.readFile ../context/base.md}
      CONTEXT

      chown ${username}:guild /home/${username}/.claude-context.md
    '';
  in lib.concatStringsSep "\n" (lib.mapAttrsToList setupUser members);
}
```

### guild-workspace.nix — Shared Workspace + Dolt

```nix
# deploy/shared/guild-workspace.nix
{ config, pkgs, lib, ... }:

{
  # Dolt SQL server — the guild ledger
  # Dolt is a MySQL-compatible database with git-like version control
  environment.systemPackages = with pkgs; [
    dolt        # Dolt CLI + server
    git
    jq
    micro       # simple editor for non-technical users
  ];

  # Dolt server as a systemd service
  systemd.services.dolt-server = {
    description = "Dolt SQL Server — Guild Ledger";
    wantedBy = [ "multi-user.target" ];
    after = [ "network.target" ];

    serviceConfig = {
      Type = "simple";
      User = "dolt";
      Group = "guild";
      WorkingDirectory = "/srv/guild/ledger";
      ExecStart = "${pkgs.dolt}/bin/dolt sql-server --host 127.0.0.1 --port 3306";
      Restart = "on-failure";
      RestartSec = 5;

      # Hardening
      ProtectHome = true;
      ProtectSystem = "strict";
      ReadWritePaths = [ "/srv/guild/ledger" ];
      PrivateTmp = true;
      NoNewPrivileges = true;
    };
  };

  # Dolt system user
  users.users.dolt = {
    isSystemUser = true;
    group = "guild";
    home = "/srv/guild/ledger";
  };

  # Create workspace directories
  systemd.tmpfiles.rules = [
    "d /srv/guild          0750 root guild -"
    "d /srv/guild/repos    0750 root guild -"
    "d /srv/guild/ledger   0770 dolt guild -"
    "d /srv/guild/formabi  0770 root guild -"   # the root repo (working copy)
  ];

  # Dolt initialization script (runs once)
  systemd.services.dolt-init = {
    description = "Initialize Dolt Guild Ledger";
    wantedBy = [ "multi-user.target" ];
    before = [ "dolt-server.service" ];
    after = [ "network.target" ];

    serviceConfig = {
      Type = "oneshot";
      User = "dolt";
      Group = "guild";
      RemainAfterExit = true;
    };

    script = ''
      cd /srv/guild/ledger

      # Only init if not already initialized
      if [ ! -d .dolt ]; then
        ${pkgs.dolt}/bin/dolt init --name "formabi" --email "guild@formabi.com"

        ${pkgs.dolt}/bin/dolt sql -q "
          CREATE TABLE IF NOT EXISTS roster (
            id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
            name VARCHAR(255) NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            github VARCHAR(255),
            region VARCHAR(50),
            started DATE NOT NULL,
            active BOOLEAN DEFAULT TRUE,
            notes TEXT
          );

          CREATE TABLE IF NOT EXISTS person_roles (
            person_id VARCHAR(36) REFERENCES roster(id),
            role VARCHAR(50) NOT NULL,
            PRIMARY KEY (person_id, role)
          );

          CREATE TABLE IF NOT EXISTS ssh_keys (
            person_id VARCHAR(36) REFERENCES roster(id),
            key_type VARCHAR(50) NOT NULL,
            public_key TEXT NOT NULL,
            PRIMARY KEY (person_id, key_type)
          );

          CREATE TABLE IF NOT EXISTS customers (
            id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
            name VARCHAR(255) UNIQUE NOT NULL,
            domain VARCHAR(255) NOT NULL,
            port INTEGER NOT NULL,
            tier VARCHAR(50) NOT NULL,
            status VARCHAR(50) DEFAULT 'active',
            provisioned DATE NOT NULL,
            notes TEXT
          );

          CREATE TABLE IF NOT EXISTS decisions (
            id VARCHAR(10) PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            date DATE NOT NULL,
            status VARCHAR(50) DEFAULT 'proposed',
            author VARCHAR(255),
            summary TEXT
          );
        "

        ${pkgs.dolt}/bin/dolt add .
        ${pkgs.dolt}/bin/dolt commit -m "initialize guild ledger schema"
      fi
    '';
  };
}
```

### guild-claude.nix — Claude Code + Agents for Everyone

```nix
# deploy/shared/guild-claude.nix
{ config, pkgs, lib, ... }:

let
  # Per-user agents command — launches a tmux session with role-scoped windows
  # Each window is a workspace for a different project/area
  # Same keybindings for everyone (Ctrl-Space prefix, Alt-1..6 to switch)

  # Rich's agents: all repos + ops tools
  richAgents = pkgs.writeShellScriptBin "agents" ''
    SESSION="agents"
    tmux kill-session -t "$SESSION" 2>/dev/null

    # Window 1: guild (root repo — company as code)
    tmux new-session -d -s "$SESSION" -n "guild" -c "/srv/guild/formabi"
    tmux set-window-option -t "$SESSION:1" window-style 'bg=#0a1a1a'
    tmux set-window-option -t "$SESSION:1" window-active-style 'bg=#0a1a1a'

    # Window 2: app (formabi-app)
    tmux new-window -t "$SESSION:2" -n "app" -c "$HOME/repos/formabi-app"
    tmux set-window-option -t "$SESSION:2" window-style 'bg=#0a1a0a'
    tmux set-window-option -t "$SESSION:2" window-active-style 'bg=#0a1a0a'

    # Window 3: cmdr (deployment + infra)
    tmux new-window -t "$SESSION:3" -n "cmdr" -c "$HOME/repos/cmdr"
    tmux set-window-option -t "$SESSION:3" window-style 'bg=#0a0a1a'
    tmux set-window-option -t "$SESSION:3" window-active-style 'bg=#0a0a1a'

    # Window 4: latice
    tmux new-window -t "$SESSION:4" -n "latice" -c "$HOME/repos/latice"
    tmux set-window-option -t "$SESSION:4" window-style 'bg=#1a150a'
    tmux set-window-option -t "$SESSION:4" window-active-style 'bg=#1a150a'

    # Window 5: surface (plans + specs)
    tmux new-window -t "$SESSION:5" -n "surface" -c "$HOME/repos/surface"
    tmux set-window-option -t "$SESSION:5" window-style 'bg=#140a1a'
    tmux set-window-option -t "$SESSION:5" window-active-style 'bg=#140a1a'

    # Window 6: ledger (Dolt)
    tmux new-window -t "$SESSION:6" -n "ledger" -c "/srv/guild/ledger"
    tmux set-window-option -t "$SESSION:6" window-style 'bg=#1a1a0f'
    tmux set-window-option -t "$SESSION:6" window-active-style 'bg=#1a1a0f'

    tmux select-window -t "$SESSION:1"
    tmux attach -t "$SESSION"
  '';

  # Louis & Mark's agents: business repos + guild + ledger
  memberAgents = pkgs.writeShellScriptBin "agents" ''
    SESSION="agents"
    tmux kill-session -t "$SESSION" 2>/dev/null

    # Window 1: guild (surface — plans, specs, strategy, company-as-code)
    tmux new-session -d -s "$SESSION" -n "guild" -c "$HOME/repos/surface"
    tmux set-window-option -t "$SESSION:1" window-style 'bg=#0a1a1a'
    tmux set-window-option -t "$SESSION:1" window-active-style 'bg=#0a1a1a'

    # Window 2: homepage (company website)
    tmux new-window -t "$SESSION:2" -n "homepage" -c "$HOME/repos/homepage"
    tmux set-window-option -t "$SESSION:2" window-style 'bg=#0a1a0a'
    tmux set-window-option -t "$SESSION:2" window-active-style 'bg=#0a1a0a'

    # Window 3: latice (Rust SOA template)
    tmux new-window -t "$SESSION:3" -n "latice" -c "$HOME/repos/latice"
    tmux set-window-option -t "$SESSION:3" window-style 'bg=#1a150a'
    tmux set-window-option -t "$SESSION:3" window-active-style 'bg=#1a150a'

    tmux select-window -t "$SESSION:1"
    tmux attach -t "$SESSION"
  '';

  # Shared tmux config — same keybindings for everyone
  guildTmuxConf = ''
    # Prefix: Ctrl-Space
    unbind C-b
    set -g prefix C-Space
    bind C-Space send-prefix

    # Mouse support (scroll, select panes, resize)
    set -g mouse on

    # Start windows at 1
    set -g base-index 1

    # --- Quick window switching (no prefix needed) ---
    bind -n M-1 select-window -t 1
    bind -n M-2 select-window -t 2
    bind -n M-3 select-window -t 3
    bind -n M-4 select-window -t 4
    bind -n M-5 select-window -t 5
    bind -n M-6 select-window -t 6
    bind -n M-Left previous-window
    bind -n M-Right next-window

    # --- Session management ---
    bind -n M-d detach-client
    bind -n M-s choose-tree -s
    bind -n M-n switch-client -n
    bind -n M-p switch-client -p

    # Split keeping cwd
    bind C-c split-window -v -c "#{pane_current_path}"
    bind C-v split-window -h -c "#{pane_current_path}"

    # Kill window
    bind w kill-window

    # Pane borders show command + path
    set -g pane-border-format "#{pane_index}: #{pane_current_command} | #{pane_current_path}"
    set -g pane-border-status top

    # Status bar — purple
    set -g status-style "bg=colour129,fg=white"
    set -g status-left "[#S] "
    set -g status-right ""
    set -g window-status-format " #I:#W "
    set -g window-status-current-format " #I:#W "
    set -g window-status-current-style "bg=colour6,fg=black,bold"
    set -g window-status-style "bg=colour129,fg=colour250"

    # Vi mode for copy/paste
    setw -g mode-keys vi
    bind -T copy-mode-vi v send-keys -X begin-selection
    bind -T copy-mode-vi y send-keys -X copy-pipe-and-cancel "xclip -selection clipboard"

    # Sync shell to sibling pane's cwd
    bind C-f run-shell 'tmux send-keys "cd \"$(tmux display-message -p -t {top} \"#{pane_current_path}\")\"" Enter'
  '';

  guildBashrc = username: ''
    export EDITOR=micro
    export VISUAL=micro

    # Friendly prompt
    parse_git_branch() {
      git branch 2>/dev/null | sed -e '/^[^*]/d' -e 's/* \(.*\)/ (\1)/'
    }
    PS1='\[\033[1;36m\]${username}@guild\[\033[0m\]:\[\033[1;34m\]\w\[\033[33m\]$(parse_git_branch)\[\033[0m\]\$ '

    # Guild aliases
    alias roster='dolt sql -q "SELECT name, email, GROUP_CONCAT(role) as roles FROM roster r JOIN person_roles pr ON r.id = pr.person_id WHERE r.active GROUP BY r.id" -r table'
    alias customers='dolt sql -q "SELECT name, domain, tier, status FROM customers WHERE status = '\''active'\''" -r table'
    alias status='cat /srv/guild/formabi/state/stage.json | jq .'
    alias priorities='cat /srv/guild/formabi/state/priorities.json | jq .'
    alias decisions='cat /srv/guild/formabi/decisions/index.json | jq .'
    alias ledger-log='cd /srv/guild/ledger && dolt log --oneline | head -20'

    guild-help() {
      echo ""
      echo "  Guild Commands"
      echo "  ─────────────────────────────────────"
      echo "  agents          Launch your workspace (tmux session with project windows)"
      echo "  claude          Open Claude Code (your AI assistant)"
      echo "  roster          Show guild members"
      echo "  customers       Show active customers"
      echo "  status          Show company stage"
      echo "  priorities      Show current priorities"
      echo "  decisions       Show decision log"
      echo "  ledger-log      Show recent ledger changes"
      echo ""
      echo "  Keyboard shortcuts (inside agents session)"
      echo "  ─────────────────────────────────────"
      echo "  Alt-1..6        Switch between project windows"
      echo "  Alt-Left/Right  Previous/next window"
      echo "  Ctrl-Space      Tmux prefix (then Ctrl-c to split, w to close)"
      echo "  Alt-d           Detach (session keeps running)"
      echo ""
      echo "  Everything else — just ask Claude."
      echo ""
    }
    alias help=guild-help
    alias halp=guild-help
  '';

in {
  # System packages
  environment.systemPackages = with pkgs; [
    nodejs_22         # required for Claude Code
    git
    micro             # simple editor
    jq
    dolt              # guild ledger CLI
    tmux
    htop
  ];

  # Install Claude Code globally
  systemd.services.install-claude-code = {
    description = "Install Claude Code CLI";
    wantedBy = [ "multi-user.target" ];
    serviceConfig = {
      Type = "oneshot";
      RemainAfterExit = true;
    };
    path = [ pkgs.nodejs_22 pkgs.git ];
    script = ''
      npm install -g @anthropic-ai/claude-code || true
    '';
  };

  # Per-user agents command (different windows per role)
  # Rich gets the full agents, Louis & Mark get the business agents
  environment.systemPackages = [
    # These are overridden per-user below via home directory bin/
  ];

  # Per-user setup: agents script + tmux config
  system.activationScripts.guildAgents = ''
    # Rich: full agents
    mkdir -p /home/rich/bin
    cp ${richAgents}/bin/agents /home/rich/bin/agents
    chmod +x /home/rich/bin/agents
    chown rich:guild /home/rich/bin/agents

    # Louis: member agents
    mkdir -p /home/louis/bin
    cp ${memberAgents}/bin/agents /home/louis/bin/agents
    chmod +x /home/louis/bin/agents
    chown louis:guild /home/louis/bin/agents

    # Mark: member agents
    mkdir -p /home/mark/bin
    cp ${memberAgents}/bin/agents /home/mark/bin/agents
    chmod +x /home/mark/bin/agents
    chown mark:guild /home/mark/bin/agents

    # Shared tmux config for all users
    for user in rich louis mark; do
      cat > /home/$user/.tmux.conf << 'TMUXCONF'
    ${guildTmuxConf}
    TMUXCONF
      chown $user:guild /home/$user/.tmux.conf
    done
  '';

  # Per-user bashrc
  environment.etc."profile.d/guild.sh" = {
    text = ''
      # Add ~/bin to PATH for agents command
      export PATH="$HOME/bin:$PATH"

      case "$USER" in
        rich)  ${guildBashrc "rich"} ;;
        louis) ${guildBashrc "louis"} ;;
        mark)  ${guildBashrc "mark"} ;;
      esac
    '';
  };
}
```

### guild-guardrails.nix — Safety for Non-Technical Users

```nix
# deploy/shared/guild-guardrails.nix
{ config, pkgs, lib, ... }:

{
  # === SUDO ===
  # Only rich (ops role → wheel group) gets sudo
  # Louis and Mark cannot sudo — period
  security.sudo = {
    enable = true;
    wheelNeedsPassword = true;  # even rich needs password for sudo
    extraRules = [
      # No additional sudo rules for non-ops users
      # They physically cannot escalate
    ];
  };

  # === FILE PERMISSIONS ===
  # /srv/guild/formabi (root repo working copy) — guild group can read+write
  # /srv/guild/ledger (Dolt) — guild group can read, dolt user can write
  # /srv/guild/repos (bare repos) — per-group read access

  # Dolt write access: only via the dolt SQL server
  # Non-technical users query Dolt through Claude, which runs `dolt sql -q`
  # They cannot corrupt the database because:
  #   1. Dolt server handles transactions
  #   2. Every change is a Dolt commit (revertible)
  #   3. Claude validates before executing

  # === TMUX: Auto-Launch Agents on SSH Login ===
  # On SSH login, automatically attach to existing agents session or launch it
  # This means: SSH in → you're immediately in your workspace
  # If SSH drops, reconnect → you're right back where you were
  programs.tmux = {
    enable = true;
    extraConfig = ''
      set -g history-limit 50000
    '';
  };

  environment.etc."profile.d/tmux-auto.sh" = {
    text = ''
      # Auto-launch agents session on SSH login
      if [ -n "$SSH_CONNECTION" ] && [ -z "$TMUX" ]; then
        # Reattach to existing agents session, or launch a fresh one
        tmux attach-session -t agents 2>/dev/null || agents
      fi
    '';
  };

  # === BACKUPS ===
  # Automatic daily backups of the guild workspace
  systemd.services.guild-backup = {
    description = "Backup guild workspace";
    startAt = "daily";
    serviceConfig = {
      Type = "oneshot";
      User = "root";
    };
    script = ''
      # Backup Dolt database
      cd /srv/guild/ledger
      ${pkgs.dolt}/bin/dolt backup sync local-backup /var/backup/guild/ledger/$(date +%Y-%m-%d) || true

      # Backup root repo
      cd /srv/guild/formabi
      ${pkgs.git}/bin/git bundle create /var/backup/guild/formabi-$(date +%Y-%m-%d).bundle --all || true

      # Keep 30 days of backups
      find /var/backup/guild/ -mtime +30 -delete || true
    '';
  };

  systemd.tmpfiles.rules = [
    "d /var/backup/guild         0700 root root -"
    "d /var/backup/guild/ledger  0700 root root -"
  ];

  # === RESOURCE LIMITS ===
  # Prevent runaway processes from one user killing the server
  systemd.services."user@".serviceConfig = {
    MemoryMax = "8G";       # per-user memory limit
    CPUQuota = "200%";      # 2 cores max per user
    TasksMax = 512;         # max processes per user
  };

  # === GIT SAFETY ===
  # System-wide git config: prevent force-pushes, set sane defaults
  environment.etc."gitconfig" = {
    text = ''
      [push]
        default = simple
      [pull]
        rebase = false
      [init]
        defaultBranch = main
      [core]
        editor = micro
      [receive]
        denyNonFastForwards = true
        denyDeletes = true
    '';
  };

  # === MOTD ===
  # Show useful info on login
  users.motd = ''

    ╔══════════════════════════════════════════╗
    ║  Formabi Guild                           ║
    ║  guild.zolanic.space                     ║
    ╚══════════════════════════════════════════╝

    Type 'claude' to start working with AI.
    Type 'help' for available commands.

  '';
}
```

### guild/configuration.nix — Server-Specific Config

```nix
# deploy/servers/guild/configuration.nix
{ config, pkgs, lib, ... }:

{
  networking.hostName = "guild";

  # Timezone
  time.timeZone = "UTC";

  # Firewall
  networking.firewall = {
    enable = true;
    allowedTCPPorts = [
      22    # SSH (primary interface)
      80    # HTTP (redirect to HTTPS)
      443   # HTTPS (Forgejo, static sites)
      2222  # Forgejo Git SSH
    ];
  };

  # Secrets (agenix)
  age.secrets = {
    # Anthropic API key for Claude Code (shared guild key)
    claude-api-key = {
      file = ../../secrets/claude-api-key.age;
      owner = "root";
      group = "guild";
      mode = "0440";
    };
    # Forgejo runner token
    forgejo-runner-token = {
      file = ../../secrets/forgejo-runner-token.age;
    };
  };

  # Make Claude API key available to all guild members
  environment.etc."guild/claude-api-key" = {
    source = config.age.secrets.claude-api-key.path;
    mode = "0440";
    group = "guild";
  };

  # PostgreSQL for Forgejo + potentially Dolt (if using MySQL mode, separate)
  services.postgresql = {
    enable = true;
    package = pkgs.postgresql_17;
  };

  # Nginx reverse proxy
  services.nginx = {
    enable = true;
    recommendedProxySettings = true;
    recommendedTlsSettings = true;
    recommendedOptimisation = true;
    recommendedGzipSettings = true;
  };

  # ACME (Let's Encrypt)
  security.acme = {
    acceptTerms = true;
    defaults.email = "rich@formabi.com";
  };

  # NixOS version
  system.stateVersion = "24.11";
}
```

## Claude Code Configuration Per User

Each guild member gets a `CLAUDE.md` in their home directory, scoped to their role. This is the key mechanism — Claude becomes a different agent depending on who's using it.

### Rich's CLAUDE.md (engineering + ops)

```markdown
# Formabi Guild — Rich (engineering, ops)

You are working on the Formabi guild server. Rich is the technical founder
with full access to all systems.

## Available
- All repos: formabi-app, latice, cmdr, deck, zolanic
- Dolt ledger: full read/write (INSERT, UPDATE, DELETE, branch, merge)
- Server config: can edit NixOS configs, deploy
- Secrets: can manage agenix secrets
- Sudo: yes (wheel group)

## Guild Ledger (Dolt)
Query: dolt sql -q "..." (from /srv/guild/ledger/)
Commit: dolt add . && dolt commit -m "..."
Log: dolt log
Diff: dolt diff

## Deploy
After config changes: deploy server (from cmdr repo)
```

### Louis & Mark's CLAUDE.md (business — shared template)

Both get the same CLAUDE.md (with their name substituted). They're generalists who wear many hats.

```markdown
# Formabi Guild — {{NAME}} (cofounder, business)

You are working on the Formabi guild server. {{NAME}} is a cofounder who
wears many hats — sales, discovery, strategy, brand, content, customer
conversations, operations, whatever's needed. He is not a programmer —
communicate clearly and handle all technical operations (git, file editing,
Dolt queries) on his behalf.

## Important
- Always explain what you're about to do before doing it
- Confirm before making changes that affect others
- Use simple language, avoid jargon
- If something goes wrong, don't panic — everything is versioned and recoverable
- When {{NAME}} asks you to do something, just do it — don't lecture about
  "best practices" or suggest he learn git commands

## What {{NAME}} can work on (everything except code + infra)
- identity/ — mission, voice, processes (the company's soul)
- brand/ — brand.json, visual identity
- state/ — stage.json, priorities.json, metrics.json (company direction)
- decisions/ — proposing and documenting decisions
- deck repo — pitch decks, handbook, sales materials
- zolanic repo — brand website content
- Guild ledger (Dolt) — customers, roster queries, adding prospects/customers

## What {{NAME}} cannot do (and that's fine)
- No sudo, no server config changes
- No access to formabi-app source code or cmdr deployment configs
- Cannot deploy the server (Rich handles infrastructure)

## Guild Ledger (Dolt)
The ledger is the company's structured data. Query and update from /srv/guild/ledger/:

  # Read
  dolt sql -q "SELECT * FROM roster WHERE active = TRUE" -r table
  dolt sql -q "SELECT * FROM customers" -r table

  # Write (always confirm with {{NAME}} first)
  dolt sql -q "INSERT INTO customers ..."
  dolt add . && dolt commit -m "description of change"

  # History
  dolt log --oneline

## Git workflow
{{NAME}}'s changes go through git. The pattern:
1. Edit files in /srv/guild/formabi/ (the root repo)
2. git add <files>
3. git commit -m "what changed and why"
4. Others will see the changes on next pull

Always write clear commit messages. {{NAME}} is shaping the company —
his commits are the audit trail.

## Typical tasks
- "Update our mission statement" → edit identity/mission.md
- "Change the brand colors" → edit brand/brand.json
- "Add a new decision about X" → create decisions/NNN-title.md + update index
- "What's our current priority?" → cat state/priorities.json
- "Who are our customers?" → dolt sql on customers table
- "Add a prospect we talked to" → INSERT into customers with status 'prospect'
- "Update the investor deck" → edit in deck repo
- "Prep me for a sales call" → read deck, customers, product info, voice.md
- "What changed this week?" → git log --oneline --since="1 week ago"
- "Draft an email to a prospect" → read voice.md + customer context
- "Document a decision we made" → create decision record
- "Update our processes" → edit identity/processes.md
```

## How It Works Day-to-Day

### Louis logs in to do some discovery work

```
louis@laptop:~$ ssh louis@guild.zolanic.space

  ╔══════════════════════════════════════════╗
  ║  Formabi Guild                           ║
  ║  guild.zolanic.space                     ║
  ╚══════════════════════════════════════════╝

  [agents session launches automatically]
  [3 windows: guild | homepage | latice]
  [starts in window 1: guild — /srv/guild/formabi/]

louis@guild:/srv/guild/formabi$ claude

> I had a great discovery call with Meridian, a compliance firm.
> They have 200 employees filling out regulatory forms monthly
> and their current process is paper + Excel. Add them as a prospect
> and help me draft a follow-up email.

  I'll add Meridian to the customer ledger first.

  [runs: INSERT INTO customers ... status='prospect', notes='compliance firm, 200 employees, paper+Excel pain']
  [dolt commit -m "add prospect: Meridian (compliance, 200 employees)"]

  Done. Now for the follow-up email — let me read our voice guide first.

  [reads identity/voice.md, deck content]

  Here's a draft:

  "Hi Sarah, great speaking today. I wanted to follow up on what you
  shared about your monthly compliance process..."

  [drafts email in formabi's voice]

> Perfect. Also, I want to update our mission statement — it doesn't
> mention regulated industries and that's clearly our sweet spot.

  [reads identity/mission.md, shows proposed edit, confirms, commits]
  Done. Committed as "update mission: emphasize regulated industries focus"
```

### Mark logs in to close a deal

```
mark@laptop:~$ ssh mark@guild.zolanic.space

  [agents session launches — guild | deck | brand | ledger]

mark@guild:/srv/guild/formabi$ claude

> Meridian said yes. They want to start a pilot next week.
> Update them and help me figure out what we need to do.

  [queries customers table]
  Found Meridian — currently listed as 'prospect'. Updating to 'active'.

  [UPDATE customers SET status = 'active' WHERE name = 'meridian']
  [dolt commit -m "activate customer: Meridian — pilot starting next week"]

  Done. For next steps:
  1. Rich needs to provision their instance on the server
  2. We should document onboarding steps in identity/processes.md
  3. You might want to log a decision about pilot terms

  Want me to draft the onboarding process doc?

> Yes, and also prep me for a call with Ashford Partners tomorrow.
> They do HR compliance, similar to Meridian.

  [drafts onboarding process, updates processes.md, commits]
  [reads deck content, customer context, product info]

  For Ashford: since they're similar to Meridian, here's the angle...
  We can reference the Meridian pilot as early traction...
```

### Rich sees what happened

```
rich@guild:~$ cd /srv/guild/ledger
rich@guild:ledger$ dolt log --oneline
abc1234 activate customer: Meridian — pilot starting next week (mark)
def5678 add prospect: Meridian (louis)
...

rich@guild:~$ cd /srv/guild/formabi
rich@guild:formabi$ git log --oneline
b3c4d5e add customer onboarding process (mark)
a1b2c3d update mission: emphasize regulated industries focus (louis)
...

# Rich provisions Meridian's instance
rich@guild:~$ cd repos/cmdr
# ... adds instance config, deploys ...
```

## Robustness: What Can Go Wrong

| Risk | Mitigation |
|------|------------|
| Louis/Mark accidentally delete a file | Git: `git checkout -- <file>` to restore. Everything versioned. |
| Bad SQL query corrupts Dolt data | Dolt: `dolt checkout .` to undo uncommitted changes, or `dolt reset --hard HEAD~1` to revert a commit. |
| SSH connection drops mid-work | tmux agents session persists. Reconnect → auto-reattaches to where you were. |
| Someone edits the same file simultaneously | Git handles merge conflicts. Claude can help resolve. |
| Non-technical user runs something dangerous | No sudo access. Unix permissions prevent touching system files. Claude's CLAUDE.md instructs it to confirm before acting. |
| Server disk fills up | Monitoring + alerts (reuse existing Prometheus setup). Resource limits per user. |
| Claude API key exhausted | Shared key with usage monitoring. Can set per-user keys if needed. |
| Someone pushes broken git state | `receive.denyNonFastForwards = true` prevents force-push. Branches are protected. |
| Need to undo a series of changes | Both git and Dolt support full history traversal. `git reflog` and `dolt log` as escape hatches. |

## What to Set Up First

### Before the server arrives
1. **Generate SSH keys** for Louis and Mark (help them through this)
2. **Create the root repo** (formabi/formabi) with identity/, brand/, state/, decisions/
3. **Seed content** — extract mission, voice, processes from existing deck/rlpt-notes
4. **Write the CLAUDE.md files** for each role

### Day 1: Server arrives
1. **Install NixOS** — base install + `nixos-generate-config` for hardware
2. **Apply guild config** — users, SSH, tmux, basic packages
3. **Install Claude Code** — verify all 3 users can run `claude`
4. **Set up Dolt** — init database, create schema, seed roster + customers
5. **Clone root repo** to /srv/guild/formabi/
6. **Test**: each person SSHs in, runs `claude`, does a basic task

### Week 1: Get comfortable
7. **Onboard Louis and Mark** — guided session where they SSH in, run claude, make their first edit
8. **Establish rhythm** — daily check-ins via the guild (everyone SSHs in, reviews what changed)
9. **Iterate on CLAUDE.md** — adjust based on what Louis and Mark actually need
10. **Set up Forgejo** — browser access for when SSH feels heavy

### Later
11. **Wire Dolt → NixOS** — roster changes automatically provision/deprovision users
12. **Wire customers → deploy** — new customers auto-provisioned
13. **Migrate formrunner services** to guild (or keep separate)
