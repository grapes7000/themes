from __future__ import annotations

import json
import os
import tempfile

PROFILE_PATH = os.path.join(os.path.expanduser("~"), ".config", "theme-engine", "starship.json")

# Nerd Font glyphs above U+FFFF need a surrogate pair once encoded to UTF-16.
# Something in the editing pipeline this file has passed through mangles a
# literal astral character typed straight into source (it silently vanishes),
# but never touches one built from its code point at runtime -- so every such
# glyph below is constructed with chr(...) instead of pasted as a literal.
_G = {
    "folder": chr(0xf024b),
    "git_branch": chr(0xf418),
    "git_state": chr(0xf062c),
    "conflicted": chr(0xf0026),
    "ahead": chr(0xf0737),
    "behind": chr(0xf072e),
    "diverged": chr(0xf14ce),
    "untracked": chr(0xf02d6),
    "stashed": chr(0xf03d7),
    "modified": chr(0xf03eb),
    "staged": chr(0xf0415),
    "renamed": chr(0xf0ab9),
    "deleted": chr(0xf01b4),
    "cmd_duration": chr(0xf051b),
    "jobs": chr(0xf070e),
    "status_fail": chr(0xf0159),
    "arrow_ok": chr(0x276f),   # ❯
    "arrow_vim": chr(0x276e),  # ❮
    "os_arch": chr(0xf303), "os_debian": chr(0xf306), "os_fedora": chr(0xf30a),
    "os_ubuntu": chr(0xf31b), "os_mint": chr(0xf30e), "os_linux": chr(0xf31a),
    "os_macos": chr(0xf179), "os_windows": chr(0xf17a),
}

DEFAULT = {
    "version": 2,
    "prompt_style": "Rounded powerline",

    # powerline connectors (roles unchanged from v1: fade-in cap, the divider
    # right after it, the divider into git, and the two possible closing caps)
    "lead_fade": "", "lead_arrow": "",
    "git_connector": "", "git_end": "", "path_end": "",

    # directory
    "path_icon": _G["folder"], "path_length": 6, "path_repo_root": True,

    # os / user@host block (new in v2 -- no per-OS icon fields; those come
    # from starship's own os.symbols table, which already covers everything
    # the spec asked for)
    "os_enabled": True,

    # git
    "branch_enabled": True, "branch_icon": _G["git_branch"],
    "state_enabled": True, "state_icon": _G["git_state"],
    "status_enabled": True,
    "status_conflicted": _G["conflicted"], "status_ahead": _G["ahead"],
    "status_behind": _G["behind"], "status_diverged": _G["diverged"],
    "status_untracked": _G["untracked"], "status_stashed": _G["stashed"],
    "status_modified": _G["modified"], "status_staged": _G["staged"],
    "status_renamed": _G["renamed"], "status_deleted": _G["deleted"],

    # dev / infra segments (new in v2 -- bundle toggles rather than one field
    # per language, or the TUI would need 20+ new rows for icons nobody tunes)
    "dev_enabled": True,        # python, nodejs, rust, golang, java, lua, php, ruby, package
    "container_enabled": True,  # docker_context, kubernetes
    "cloud_enabled": True,      # terraform, nix_shell, conda, aws, gcloud, azure

    # right-side indicators
    "duration_enabled": True, "duration_icon": _G["cmd_duration"], "duration_min_ms": 2000,
    "cmd_status_enabled": True, "cmd_status_icon": _G["status_fail"],
    "jobs_enabled": True, "jobs_icon": _G["jobs"],
    "battery_enabled": True,                      # new in v2
    "memory_enabled": True, "memory_threshold": 75,  # new in v2
    "time_enabled": True,                          # new in v2

    # line-2 prompt character
    "success_symbol": _G["arrow_ok"], "error_symbol": _G["arrow_ok"], "vim_symbol": _G["arrow_vim"],
}


def profile():
    values = dict(DEFAULT)
    try:
        with open(PROFILE_PATH) as file:
            raw = json.load(file)
    except (OSError, json.JSONDecodeError):
        return values
    if not isinstance(raw, dict) or raw.get("version") != 2:
        return values
    for key, default in DEFAULT.items():
        value = raw.get(key, default)
        if type(value) is type(default):
            values[key] = value
    return values


def save(values):
    out = {key: values.get(key, default) for key, default in DEFAULT.items()}
    directory = os.path.dirname(PROFILE_PATH)
    os.makedirs(directory, exist_ok=True)
    handle, temporary = tempfile.mkstemp(prefix="starship.", suffix=".json", dir=directory)
    try:
        with os.fdopen(handle, "w") as file:
            json.dump(out, file, indent=2, ensure_ascii=False)
            file.write("\n")
        os.replace(temporary, PROFILE_PATH)
    except OSError:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


def render(colors, settings=None):
    """Two-line, Powerlevel10k-style prompt.

    Line 1: [cap][os][user][host] -> [directory] -> [git] -> [dev/infra]
    Line 2: `╰─ ❯` (or the error/vim variant), with duration/status/jobs/
            battery/time in `right_format` instead of crowding the left side.

    `colors` is the theme's role dict (bg/bg_alt/text/text_dim/accent/accent2/
    urgent/...); every hex value in the output comes from it, never hardcoded.
    `settings` is a profile dict from `profile()` -- only the pieces a user
    would plausibly want to retune (icons, thresholds, on/off toggles) are
    read from it. Which *modules exist* and how segments connect is fixed
    here, same as v1.
    """
    p = profile() if settings is None else settings
    t = lambda key: str(p[key])   # noqa: E731 -- tiny, used a dozen times below
    on = lambda key: bool(p[key])  # noqa: E731

    # --- git block: only assembled if at least one git sub-module is on ---
    git = ("$git_branch" if on("branch_enabled") else "") + \
          ("$git_state" if on("state_enabled") else "") + \
          ("$git_status" if on("status_enabled") else "")
    git_custom = ""
    if git:
        git = f"${{custom.git_connector}}{git}${{custom.git_end}}"
        git_custom = f'''
[custom.git_connector]
command = "printf x"
when = "git rev-parse --is-inside-work-tree >/dev/null 2>&1"
format = "[{t('git_connector')}](fg:accent bg:accent2)"

[custom.git_end]
command = "printf x"
when = "git rev-parse --is-inside-work-tree >/dev/null 2>&1"
format = "[{t('git_end')}](fg:accent2)"'''

    # --- dev / infra bundles: emitted as format placeholders only when on,
    # so a disabled bundle costs nothing (no empty conditionals to evaluate)
    dev = "$python$nodejs$rust$golang$java$lua$php$ruby$package" if on("dev_enabled") else ""
    container = "$docker_context$kubernetes" if on("container_enabled") else ""
    cloud = "$terraform$nix_shell$conda$aws$gcloud$azure" if on("cloud_enabled") else ""

    os_block = "$os$username$hostname" if on("os_enabled") else "$username$hostname"

    right = "".join([
        "$cmd_duration" if on("duration_enabled") else "",
        "$status" if on("cmd_status_enabled") else "",
        "$jobs" if on("jobs_enabled") else "",
        "$battery" if on("battery_enabled") else "",
        "$time" if on("time_enabled") else "",
    ])

    return f'''# AUTO-GENERATED by `theme`
"$schema" = 'https://starship.rs/config-schema.json'
add_newline = false
palette = "theme"

format = """
[{t('lead_fade')}](fg:surface){os_block}[ ](bg:surface)[{t('lead_arrow')}](fg:surface bg:accent)\
$directory\
{git}${{custom.path_end}}\
{dev}{container}{cloud}$memory_usage\
$line_break$character"""

right_format = """{right}"""

[palettes.theme]
bg = "{colors['bg']}"
surface = "{colors['bg_alt']}"
fg = "{colors['text']}"
muted = "{colors['text_dim']}"
accent = "{colors['accent']}"
accent2 = "{colors['accent2']}"
urgent = "{colors['urgent']}"
warn = "{colors.get('ansi_yellow', colors['accent'])}"

[os]
disabled = {str(not on('os_enabled')).lower()}
format = "[ $symbol]($style)"
style = "bold fg:accent bg:surface"

[os.symbols]
Arch = "{_G['os_arch']} "
CachyOS = "{_G['os_arch']} "
Debian = "{_G['os_debian']} "
Fedora = "{_G['os_fedora']} "
Ubuntu = "{_G['os_ubuntu']} "
Mint = "{_G['os_mint']} "
Linux = "{_G['os_linux']} "
Macos = "{_G['os_macos']} "
Windows = "{_G['os_windows']} "

[username]
format = "[$user]($style)"
style_user = "bold fg:fg bg:surface"
style_root = "bold fg:urgent bg:surface"
show_always = false

[hostname]
ssh_only = true
trim_at = "."
format = "[@$hostname ]($style)"
style = "bold fg:accent2 bg:surface"

[directory]
format = "[ {t('path_icon')} $path ]($style)"
style = "bold fg:bg bg:accent"
truncation_length = {int(p['path_length'])}
truncate_to_repo = {str(on('path_repo_root')).lower()}

[directory.substitutions]
"Documents" = "9 Documents"
"Downloads" = "a Downloads"
"Pictures" = "9 Pictures"
".config" = "3 .config"
{git_custom}

[custom.path_end]
command = "printf x"
when = "! git rev-parse --is-inside-work-tree >/dev/null 2>&1"
format = "[{t('path_end')}](fg:accent)"

[git_branch]
disabled = {str(not on('branch_enabled')).lower()}
symbol = "{t('branch_icon')} "
format = "[$symbol$branch(:$remote_branch) ]($style)"
style = "bold fg:bg bg:accent2"

[git_state]
disabled = {str(not on('state_enabled')).lower()}
format = "[{t('state_icon')} $state( $progress_current/$progress_total) ]($style)"
style = "bold fg:urgent bg:accent2"

[git_status]
disabled = {str(not on('status_enabled')).lower()}
format = "([$all_status$ahead_behind]($style)) "
style = "bold fg:bg bg:accent2"
conflicted = "[{t('status_conflicted')} ${{count}}](bold fg:bg bg:urgent) "
ahead = "{t('status_ahead')}${{count}} "
behind = "{t('status_behind')}${{count}} "
diverged = "{t('status_diverged')}⇡${{ahead_count}}⇣${{behind_count}} "
untracked = "{t('status_untracked')}${{count}} "
stashed = "{t('status_stashed')}${{count}} "
modified = "{t('status_modified')}${{count}} "
staged = "{t('status_staged')}${{count}} "
renamed = "{t('status_renamed')}${{count}} "
deleted = "[{t('status_deleted')}${{count}}](bold fg:bg bg:urgent) "

[python]
symbol = " "
format = "[$symbol$version ](bold accent2)"

[nodejs]
symbol = " "
format = "[$symbol$version ](bold accent2)"

[rust]
symbol = " "
format = "[$symbol$version ](bold accent2)"

[golang]
symbol = " "
format = "[$symbol$version ](bold accent2)"

[java]
symbol = " "
format = "[$symbol$version ](bold accent2)"

[lua]
symbol = " "
format = "[$symbol$version ](bold accent2)"

[php]
symbol = " "
format = "[$symbol$version ](bold accent2)"

[ruby]
symbol = " "
format = "[$symbol$version ](bold accent2)"

[package]
symbol = "6 "
format = "[$symbol$version ](bold muted)"

[docker_context]
symbol = "8 "
format = "[$symbol$context ](bold muted)"

[kubernetes]
disabled = false
symbol = "e "
format = "[$symbol$context( \\\\($namespace\\\\)) ](bold accent2)"
detect_files = ["Chart.yaml", "kustomization.yaml", "skaffold.yaml"]
detect_folders = [".kube", "k8s"]

[terraform]
symbol = "2 "
format = "[$symbol$workspace ](bold muted)"

[nix_shell]
symbol = "5 "
format = "[$symbol$state ](bold muted)"

[conda]
symbol = " "
format = "[$symbol$environment ](bold muted)"
ignore_base = true

[aws]
symbol = "f "
format = "[$symbol$profile ](bold accent)"

[gcloud]
symbol = "6 "
format = "[$symbol$account ](bold accent)"

[azure]
disabled = false
symbol = "5 "
format = "[$symbol$subscription ](bold accent)"

[memory_usage]
disabled = {str(not on('memory_enabled')).lower()}
threshold = {int(p['memory_threshold'])}
symbol = "b "
format = "[$symbol$ram ](bold urgent)"

[cmd_duration]
disabled = {str(not on('duration_enabled')).lower()}
min_time = {int(p['duration_min_ms'])}
format = "[{t('duration_icon')} $duration ](bold accent2)"

[status]
disabled = {str(not on('cmd_status_enabled')).lower()}
success_symbol = ""
format = "[{t('cmd_status_icon')} $status ](bold urgent)"

[jobs]
disabled = {str(not on('jobs_enabled')).lower()}
symbol = "{t('jobs_icon')} "
format = "[$symbol$number ](bold accent2)"

[[battery.display]]
threshold = 10
style = "bold fg:bg bg:urgent"
discharging_symbol = "e "

[[battery.display]]
threshold = 30
style = "bold fg:bg bg:warn"
discharging_symbol = "b "

[[battery.display]]
threshold = 60
style = "fg:bg bg:accent2"

[battery]
disabled = {str(not on('battery_enabled')).lower()}
full_symbol = "9 "
charging_symbol = "4 "
discharging_symbol = "9 "
format = "[$symbol$percentage% ]($style)"

[time]
disabled = {str(not on('time_enabled')).lower()}
time_format = "%I:%M %p"
format = "[  $time](bold muted)"

[character]
success_symbol = "[╰─ {t('success_symbol')}](bold accent)"
error_symbol = "[╰─ {t('error_symbol')}](bold urgent)"
vimcmd_symbol = "[╰─ {t('vim_symbol')}](bold accent2)"
vimcmd_replace_one_symbol = "[╰─ {t('vim_symbol')}](bold urgent)"
vimcmd_replace_symbol = "[╰─ {t('vim_symbol')}](bold urgent)"
vimcmd_visual_symbol = "[╰─ {t('vim_symbol')}](bold accent2)"
'''
