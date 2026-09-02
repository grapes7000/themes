from __future__ import annotations

import json
import os
import tempfile

PROFILE_PATH = os.path.join(os.path.expanduser("~"), ".config", "theme-engine", "starship.json")

# Nerd Font glyphs above U+FFFF are built from code points so they survive
# editors/pipelines that occasionally mangle literal astral characters.
_G = {
    "folder": chr(0xF024B),
    "git_branch": chr(0xF0418),
    "git_state": chr(0xF062C),
    "git_commit": chr(0xF0718),
    "git_age": chr(0xF051B),
    "project_status": chr(0xF04E1),
    "conflicted": chr(0xF0026),
    "ahead": chr(0xF0737),
    "behind": chr(0xF072E),
    "diverged": chr(0xF14CE),
    "untracked": chr(0xF02D6),
    "stashed": chr(0xF03D7),
    "modified": chr(0xF03EB),
    "staged": chr(0xF0415),
    "renamed": chr(0xF0AB9),
    "deleted": chr(0xF01B4),
    "cmd_duration": chr(0xF051B),
    "jobs": chr(0xF070E),
    "status_fail": chr(0xF0159),
    "arrow_ok": chr(0x276F),
    "arrow_vim": chr(0x276E),
    "os_arch": chr(0xF0303), "os_debian": chr(0xF0306), "os_fedora": chr(0xF030A),
    "os_ubuntu": chr(0xF031B), "os_mint": chr(0xF030E), "os_linux": chr(0xF031A),
    "os_macos": chr(0xF0179), "os_windows": chr(0xF017A),
    "python": chr(0xE73C), "nodejs": chr(0xE718), "rust": chr(0xE7A8), "golang": chr(0xE627),
    "java": chr(0xE738), "lua": chr(0xE620), "php": chr(0xE73D), "ruby": chr(0xE739),
    "package": chr(0xF03D6), "docker": chr(0xF0868), "kubernetes": chr(0xF10FE),
    "terraform": chr(0xF1062), "nix": chr(0xF1105), "conda": chr(0xF0C3),
    "aws": chr(0xF0E0F), "azure": chr(0xF0805), "gcloud": chr(0xF11F6),
    "memory": chr(0xF035B), "time": chr(0xF017),
    "batt_full": chr(0xF0079), "batt_charge": chr(0xF0084),
    "batt_low": chr(0xF007B),
    "doc_ico": chr(0xF0219), "dl_ico": chr(0xF01DA), "pic_ico": chr(0xF02E9), "cfg_ico": chr(0xF0493),
}

STYLE_NAMES = ("workspace", "minimal", "hud", "neon", "operator")
STYLE_DESCRIPTIONS = {
    "workspace": "full two-line powerline workspace prompt with rich Git detail",
    "minimal": "quiet directory + Git prompt that only surfaces useful status",
    "hud": "single-line dashboard with a dynamic fill bridge and telemetry",
    "neon": "transparent cyber variant of workspace with thin separators",
    "operator": "repo console with commit age and optional .starship-status signal",
}

_STYLE_ALIASES = {
    "rounded powerline": "workspace",
    "powerlevel10k workspace": "workspace",
    "focused development": "neon",
    "minimal status": "minimal",
}

DEFAULT = {
    "version": 3,
    "prompt_style": "workspace",
    "lead_fade": "", "lead_arrow": "",
    "git_connector": "", "git_end": "", "path_end": "",
    "path_icon": _G["folder"], "path_length": 6, "path_repo_root": True,
    "os_enabled": True,
    "branch_enabled": True, "branch_icon": _G["git_branch"],
    "state_enabled": True, "state_icon": _G["git_state"],
    "status_enabled": True,
    "status_conflicted": _G["conflicted"], "status_ahead": _G["ahead"],
    "status_behind": _G["behind"], "status_diverged": _G["diverged"],
    "status_untracked": _G["untracked"], "status_stashed": _G["stashed"],
    "status_modified": _G["modified"], "status_staged": _G["staged"],
    "status_renamed": _G["renamed"], "status_deleted": _G["deleted"],
    "dev_enabled": True,
    "container_enabled": True,
    "cloud_enabled": True,
    "duration_enabled": True, "duration_icon": _G["cmd_duration"], "duration_min_ms": 2000,
    "cmd_status_enabled": True, "cmd_status_icon": _G["status_fail"],
    "jobs_enabled": True, "jobs_icon": _G["jobs"],
    "battery_enabled": True,
    "memory_enabled": True, "memory_threshold": 75,
    "time_enabled": True,
    "success_symbol": _G["arrow_ok"], "error_symbol": _G["arrow_ok"], "vim_symbol": _G["arrow_vim"],
}

# Switching styles intentionally applies a coherent module set. The detailed
# icon/threshold values remain user-editable and are preserved.
STYLE_PRESETS = {
    "workspace": {
        "os_enabled": True, "dev_enabled": True, "container_enabled": True, "cloud_enabled": True,
        "duration_enabled": True, "cmd_status_enabled": True, "jobs_enabled": True,
        "battery_enabled": True, "memory_enabled": True, "time_enabled": True,
    },
    "minimal": {
        "os_enabled": False, "dev_enabled": False, "container_enabled": False, "cloud_enabled": False,
        "duration_enabled": True, "cmd_status_enabled": True, "jobs_enabled": False,
        "battery_enabled": False, "memory_enabled": False, "time_enabled": False,
    },
    "hud": {
        "os_enabled": True, "dev_enabled": True, "container_enabled": False, "cloud_enabled": False,
        "duration_enabled": True, "cmd_status_enabled": True, "jobs_enabled": True,
        "battery_enabled": True, "memory_enabled": False, "time_enabled": True,
    },
    "neon": {
        "os_enabled": True, "dev_enabled": True, "container_enabled": True, "cloud_enabled": False,
        "duration_enabled": True, "cmd_status_enabled": True, "jobs_enabled": True,
        "battery_enabled": True, "memory_enabled": False, "time_enabled": True,
    },
    "operator": {
        "os_enabled": True, "dev_enabled": True, "container_enabled": True, "cloud_enabled": True,
        "duration_enabled": True, "cmd_status_enabled": True, "jobs_enabled": True,
        "battery_enabled": True, "memory_enabled": False, "time_enabled": True,
    },
}


def normalize_style(name: object) -> str:
    value = str(name or "workspace").strip().lower()
    value = _STYLE_ALIASES.get(value, value)
    return value if value in STYLE_NAMES else "workspace"


def apply_style(values: dict, name: str) -> dict:
    style = normalize_style(name)
    out = dict(DEFAULT)
    for key, default in DEFAULT.items():
        value = values.get(key, default)
        if type(value) is type(default):
            out[key] = value
    out["prompt_style"] = style
    out.update(STYLE_PRESETS[style])
    return out


def profile() -> dict:
    values = dict(DEFAULT)
    try:
        with open(PROFILE_PATH, encoding="utf-8") as file:
            raw = json.load(file)
    except (OSError, json.JSONDecodeError):
        return values
    if not isinstance(raw, dict):
        return values
    for key, default in DEFAULT.items():
        if key == "version":
            continue
        value = raw.get(key, default)
        if type(value) is type(default):
            values[key] = value
    values["prompt_style"] = normalize_style(values.get("prompt_style"))
    return values


def save(values: dict) -> None:
    out = {key: values.get(key, default) for key, default in DEFAULT.items()}
    out["version"] = DEFAULT["version"]
    out["prompt_style"] = normalize_style(out.get("prompt_style"))
    directory = os.path.dirname(PROFILE_PATH)
    os.makedirs(directory, exist_ok=True)
    handle, temporary = tempfile.mkstemp(prefix="starship.", suffix=".json", dir=directory)
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as file:
            json.dump(out, file, indent=2, ensure_ascii=False)
            file.write("\n")
        os.replace(temporary, PROFILE_PATH)
    except OSError:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


def _bool(value: object) -> str:
    return str(bool(value)).lower()


def _palette(colors: dict) -> str:
    return f'''[palettes.theme]
bg = "{colors['bg']}"
surface = "{colors['bg_alt']}"
fg = "{colors['text']}"
muted = "{colors['text_dim']}"
accent = "{colors['accent']}"
accent2 = "{colors['accent2']}"
urgent = "{colors['urgent']}"
warn = "{colors.get('ansi_yellow', colors['accent'])}"
success = "{colors.get('ansi_green', colors['accent2'])}"
'''


def _os_symbols() -> str:
    return f'''[os.symbols]
Arch = "{_G['os_arch']} "
CachyOS = "{_G['os_arch']} "
Debian = "{_G['os_debian']} "
Fedora = "{_G['os_fedora']} "
Ubuntu = "{_G['os_ubuntu']} "
Mint = "{_G['os_mint']} "
Linux = "{_G['os_linux']} "
Macos = "{_G['os_macos']} "
Windows = "{_G['os_windows']} "
'''


def _dev_modules() -> str:
    return f'''[python]
symbol = "{_G['python']} "
format = "[$symbol$version ](bold fg:accent2)"
[nodejs]
symbol = "{_G['nodejs']} "
format = "[$symbol$version ](bold fg:accent2)"
[rust]
symbol = "{_G['rust']} "
format = "[$symbol$version ](bold fg:accent2)"
[golang]
symbol = "{_G['golang']} "
format = "[$symbol$version ](bold fg:accent2)"
[java]
symbol = "{_G['java']} "
format = "[$symbol$version ](bold fg:accent2)"
[lua]
symbol = "{_G['lua']} "
format = "[$symbol$version ](bold fg:accent2)"
[php]
symbol = "{_G['php']} "
format = "[$symbol$version ](bold fg:accent2)"
[ruby]
symbol = "{_G['ruby']} "
format = "[$symbol$version ](bold fg:accent2)"
[package]
symbol = "{_G['package']} "
format = "[$symbol$version ](bold fg:muted)"
[docker_context]
symbol = "{_G['docker']} "
format = "[$symbol$context ](bold fg:muted)"
[kubernetes]
disabled = false
symbol = "{_G['kubernetes']} "
format = '[$symbol$context( \\($namespace\\)) ](bold fg:accent2)'
detect_files = ["Chart.yaml", "kustomization.yaml", "skaffold.yaml"]
detect_folders = [".kube", "k8s"]
[terraform]
symbol = "{_G['terraform']} "
format = "[$symbol$workspace ](bold fg:muted)"
[nix_shell]
symbol = "{_G['nix']} "
format = "[$symbol$state ](bold fg:muted)"
[conda]
symbol = "{_G['conda']} "
format = "[$symbol$environment ](bold fg:muted)"
ignore_base = true
[aws]
symbol = "{_G['aws']} "
format = "[$symbol$profile ](bold fg:accent)"
[gcloud]
symbol = "{_G['gcloud']} "
format = "[$symbol$account ](bold fg:accent)"
[azure]
disabled = false
symbol = "{_G['azure']} "
format = "[$symbol$subscription ](bold fg:accent)"
'''


def _telemetry(p: dict, *, right_padding: bool = True) -> str:
    pad = " " if right_padding else ""
    return f'''[memory_usage]
disabled = {_bool(not p['memory_enabled'])}
threshold = {int(p['memory_threshold'])}
symbol = "{_G['memory']} "
format = "[{pad}$symbol$ram](bold fg:urgent)"

[cmd_duration]
disabled = {_bool(not p['duration_enabled'])}
min_time = {int(p['duration_min_ms'])}
format = "[{pad}{p['duration_icon']} $duration](bold fg:fg)"

[status]
disabled = {_bool(not p['cmd_status_enabled'])}
success_symbol = ""
format = "[{pad}{p['cmd_status_icon']} $status](bold fg:urgent)"

[jobs]
disabled = {_bool(not p['jobs_enabled'])}
symbol = "{p['jobs_icon']} "
format = "[{pad}$symbol$number](bold fg:accent)"

[[battery.display]]
threshold = 20
style = "bold fg:urgent"
discharging_symbol = "{_G['batt_low']} "

[[battery.display]]
threshold = 100
style = "bold fg:fg"

[battery]
disabled = {_bool(not p['battery_enabled'])}
full_symbol = "{_G['batt_full']} "
charging_symbol = "{_G['batt_charge']} "
discharging_symbol = "{_G['batt_full']} "
format = "[{pad}$symbol$percentage]($style)"

[time]
disabled = {_bool(not p['time_enabled'])}
time_format = "%I:%M %p"
format = "[{pad}{_G['time']} $time](bold fg:warn)"
'''


def _git_status_block(p: dict, *, background: str | None = None) -> str:
    bg = f" bg:{background}" if background else ""
    default_style = f"bold fg:bg{bg}" if background else "bold fg:accent2"
    urgent_style = f"bold fg:bg bg:urgent" if background else "bold fg:urgent"
    return f'''[git_state]
disabled = {_bool(not p['state_enabled'])}
format = "[{p['state_icon']} $state( $progress_current/$progress_total) ]($style)"
style = "bold fg:urgent{bg}"

[git_status]
disabled = {_bool(not p['status_enabled'])}
format = "([$all_status$ahead_behind]($style))"
style = "{default_style}"
conflicted = "[{p['status_conflicted']} ${{count}}]({urgent_style}) "
ahead = "{p['status_ahead']}${{count}} "
behind = "{p['status_behind']}${{count}} "
diverged = "{p['status_diverged']}⇡${{ahead_count}}⇣${{behind_count}} "
untracked = "{p['status_untracked']}${{count}} "
stashed = "{p['status_stashed']}${{count}} "
modified = "{p['status_modified']}${{count}} "
staged = "{p['status_staged']}${{count}} "
renamed = "{p['status_renamed']}${{count}} "
deleted = "[{p['status_deleted']}${{count}}]({urgent_style}) "
'''


def _workspace(p: dict, colors: dict) -> str:
    git = "$git_branch$git_commit$git_state$git_status$git_metrics"
    dev = "$python$nodejs$rust$golang$java$lua$php$ruby$package" if p["dev_enabled"] else ""
    container = "$docker_context$kubernetes" if p["container_enabled"] else ""
    cloud = "$terraform$nix_shell$conda$aws$gcloud$azure" if p["cloud_enabled"] else ""
    os_block = "$os$username$hostname" if p["os_enabled"] else "$username$hostname"
    right = "".join([
        "$status" if p["cmd_status_enabled"] else "",
        "$cmd_duration" if p["duration_enabled"] else "",
        "$jobs" if p["jobs_enabled"] else "",
        "$battery" if p["battery_enabled"] else "",
        "$time" if p["time_enabled"] else "",
    ])
    return f'''# AUTO-GENERATED by `theme`
# STARSHIP_STYLE = workspace
"$schema" = 'https://starship.rs/config-schema.json'
add_newline = false
scan_timeout = 30
command_timeout = 500
palette = "theme"
format = """
[{p['lead_fade']}](fg:surface){os_block}[ ](bg:surface)[{p['lead_arrow']}](fg:surface bg:accent)\
$directory\
${{custom.git_connector}}{git}${{custom.git_end}}${{custom.path_end}}\
{dev}{container}{cloud}$memory_usage\
$line_break$character"""
right_format = """({right})"""

{_palette(colors)}
[os]
disabled = {_bool(not p['os_enabled'])}
format = "[ $symbol]($style)"
style = "bold fg:accent bg:surface"
{_os_symbols()}
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
format = "[ {p['path_icon']} $path ]($style)"
style = "bold fg:bg bg:accent"
truncation_length = {int(p['path_length'])}
truncate_to_repo = {_bool(p['path_repo_root'])}
[directory.substitutions]
"Documents" = "{_G['doc_ico']} Documents"
"Downloads" = "{_G['dl_ico']} Downloads"
"Pictures" = "{_G['pic_ico']} Pictures"
".config" = "{_G['cfg_ico']} .config"

[custom.git_connector]
command = "printf x"
when = "git rev-parse --is-inside-work-tree >/dev/null 2>&1"
format = "[{p['git_connector']}](fg:accent bg:accent2)"
[custom.git_end]
command = "printf x"
when = "git rev-parse --is-inside-work-tree >/dev/null 2>&1"
format = "[{p['git_end']}](fg:accent2)"
[custom.path_end]
command = "printf x"
when = "! git rev-parse --is-inside-work-tree >/dev/null 2>&1"
format = "[{p['path_end']}](fg:accent)"

[git_branch]
disabled = {_bool(not p['branch_enabled'])}
symbol = "{p['branch_icon']} "
format = "[$symbol$branch(:$remote_branch) ]($style)"
style = "bold fg:bg bg:accent2"
[git_commit]
commit_hash_length = 6
only_detached = false
tag_disabled = false
tag_symbol = " 󰓹 "
format = "[{_G['git_commit']} $hash$tag ](bold fg:bg bg:accent2)"
{_git_status_block(p, background='accent2')}
[git_metrics]
disabled = false
only_nonzero_diffs = true
format = "([+$added](bold fg:success bg:accent2) )([-$deleted](bold fg:urgent bg:accent2) )"

{_dev_modules()}
{_telemetry(p)}
[character]
success_symbol = "[╰─ {p['success_symbol']}](bold fg:accent)"
error_symbol = "[╰─ {p['error_symbol']}](bold fg:urgent)"
vimcmd_symbol = "[╰─ {p['vim_symbol']}](bold fg:accent2)"
vimcmd_replace_one_symbol = "[╰─ {p['vim_symbol']}](bold fg:urgent)"
vimcmd_replace_symbol = "[╰─ {p['vim_symbol']}](bold fg:urgent)"
vimcmd_visual_symbol = "[╰─ {p['vim_symbol']}](bold fg:accent2)"
'''


def _minimal(p: dict, colors: dict) -> str:
    right = "".join(["$status" if p["cmd_status_enabled"] else "", "$cmd_duration" if p["duration_enabled"] else ""])
    return f'''# AUTO-GENERATED by `theme`
# STARSHIP_STYLE = minimal
"$schema" = 'https://starship.rs/config-schema.json'
add_newline = false
scan_timeout = 20
command_timeout = 300
palette = "theme"
format = """$hostname$directory$git_branch$git_state$git_status$line_break$character"""
right_format = """({right})"""

{_palette(colors)}
[hostname]
ssh_only = true
format = "[@$hostname ](bold fg:muted)"
[directory]
format = "[{p['path_icon']} $path](bold fg:accent) "
truncation_length = {max(3, int(p['path_length']))}
truncate_to_repo = {_bool(p['path_repo_root'])}
[git_branch]
disabled = {_bool(not p['branch_enabled'])}
symbol = "{p['branch_icon']} "
format = "[$symbol$branch](bold fg:accent2) "
{_git_status_block(p)}
{_telemetry(p, right_padding=False)}
[character]
success_symbol = "[{p['success_symbol']}](bold fg:accent)"
error_symbol = "[{p['error_symbol']}](bold fg:urgent)"
vimcmd_symbol = "[{p['vim_symbol']}](bold fg:accent2)"
'''


def _hud(p: dict, colors: dict) -> str:
    dev = "$python$nodejs$rust$golang$java$lua$php$ruby" if p["dev_enabled"] else ""
    right = "".join([
        "$status" if p["cmd_status_enabled"] else "",
        "$cmd_duration" if p["duration_enabled"] else "",
        "$jobs" if p["jobs_enabled"] else "",
        "$battery" if p["battery_enabled"] else "",
        "$time" if p["time_enabled"] else "",
    ])
    return f'''# AUTO-GENERATED by `theme`
# STARSHIP_STYLE = hud
"$schema" = 'https://starship.rs/config-schema.json'
add_newline = false
scan_timeout = 30
command_timeout = 500
palette = "theme"
format = """$os$directory$git_branch$git_status$git_metrics{dev}$fill{right}$line_break$character"""
right_format = ""

{_palette(colors)}
[fill]
symbol = "·"
style = "fg:muted"
[os]
disabled = {_bool(not p['os_enabled'])}
format = "[$symbol](bold fg:accent) "
{_os_symbols()}
[directory]
format = "[{p['path_icon']} $path](bold fg:fg) "
truncation_length = {int(p['path_length'])}
truncate_to_repo = {_bool(p['path_repo_root'])}
[git_branch]
disabled = {_bool(not p['branch_enabled'])}
symbol = "{p['branch_icon']} "
format = "[$symbol$branch](bold fg:accent2) "
[git_status]
disabled = {_bool(not p['status_enabled'])}
format = "[$all_status$ahead_behind](bold fg:urgent) "
conflicted = "{p['status_conflicted']}${{count}} "
ahead = "{p['status_ahead']}${{count}} "
behind = "{p['status_behind']}${{count}} "
diverged = "{p['status_diverged']}⇡${{ahead_count}}⇣${{behind_count}} "
untracked = "{p['status_untracked']}${{count}} "
stashed = "{p['status_stashed']}${{count}} "
modified = "{p['status_modified']}${{count}} "
staged = "{p['status_staged']}${{count}} "
renamed = "{p['status_renamed']}${{count}} "
deleted = "{p['status_deleted']}${{count}} "
[git_metrics]
disabled = false
only_nonzero_diffs = true
format = "([+$added](bold fg:success) )([-$deleted](bold fg:urgent) )"
{_dev_modules()}
{_telemetry(p)}
[character]
success_symbol = "[╰─ {p['success_symbol']}](bold fg:accent)"
error_symbol = "[╰─ {p['error_symbol']}](bold fg:urgent)"
vimcmd_symbol = "[╰─ {p['vim_symbol']}](bold fg:accent2)"
'''


def _neon(p: dict, colors: dict) -> str:
    dev = "$python$nodejs$rust$golang$java$lua$php$ruby$package" if p["dev_enabled"] else ""
    container = "$docker_context$kubernetes" if p["container_enabled"] else ""
    right = "".join([
        "$status" if p["cmd_status_enabled"] else "",
        "$cmd_duration" if p["duration_enabled"] else "",
        "$jobs" if p["jobs_enabled"] else "",
        "$battery" if p["battery_enabled"] else "",
        "$time" if p["time_enabled"] else "",
    ])
    return f'''# AUTO-GENERATED by `theme`
# STARSHIP_STYLE = neon
"$schema" = 'https://starship.rs/config-schema.json'
add_newline = false
scan_timeout = 30
command_timeout = 500
palette = "theme"
format = """$os$username$hostname$directory${{custom.neon_sep}}$git_branch$git_commit$git_status$git_metrics${{custom.neon_sep_git}}{dev}{container}$line_break$character"""
right_format = """({right})"""

{_palette(colors)}
[os]
disabled = {_bool(not p['os_enabled'])}
format = "[$symbol](bold fg:accent)"
{_os_symbols()}
[username]
show_always = false
format = "[$user](bold fg:fg)"
[hostname]
ssh_only = true
format = "[@$hostname](bold fg:accent2)"
[directory]
format = "[ {p['path_icon']} $path](bold fg:accent)"
truncation_length = {int(p['path_length'])}
truncate_to_repo = {_bool(p['path_repo_root'])}
[custom.neon_sep]
command = "printf x"
when = "git rev-parse --is-inside-work-tree >/dev/null 2>&1"
format = " [](fg:muted) "
[custom.neon_sep_git]
command = "printf x"
when = "git rev-parse --is-inside-work-tree >/dev/null 2>&1"
format = "[](fg:muted) "
[git_branch]
disabled = {_bool(not p['branch_enabled'])}
symbol = "{p['branch_icon']} "
format = "[$symbol$branch](bold fg:accent2) "
[git_commit]
commit_hash_length = 5
only_detached = false
tag_disabled = false
tag_symbol = " 󰓹 "
format = "[{_G['git_commit']} $hash$tag](fg:muted) "
{_git_status_block(p)}
[git_metrics]
disabled = false
format = "([+$added](fg:success) )([-$deleted](fg:urgent) )"
{_dev_modules()}
{_telemetry(p)}
[character]
success_symbol = "[╰─](fg:muted) [{p['success_symbol']}](bold fg:accent)"
error_symbol = "[╰─](fg:muted) [{p['error_symbol']}](bold fg:urgent)"
vimcmd_symbol = "[╰─](fg:muted) [{p['vim_symbol']}](bold fg:accent2)"
'''


def _operator(p: dict, colors: dict) -> str:
    dev = "$python$nodejs$rust$golang$java$lua$php$ruby$package" if p["dev_enabled"] else ""
    container = "$docker_context$kubernetes" if p["container_enabled"] else ""
    cloud = "$terraform$nix_shell$conda$aws$gcloud$azure" if p["cloud_enabled"] else ""
    right = "".join([
        "$status" if p["cmd_status_enabled"] else "",
        "$cmd_duration" if p["duration_enabled"] else "",
        "$jobs" if p["jobs_enabled"] else "",
        "$battery" if p["battery_enabled"] else "",
        "$time" if p["time_enabled"] else "",
    ])
    return f'''# AUTO-GENERATED by `theme`
# STARSHIP_STYLE = operator
"$schema" = 'https://starship.rs/config-schema.json'
add_newline = false
scan_timeout = 30
command_timeout = 700
palette = "theme"
format = """[╭─](fg:muted) $os$directory$git_branch$git_commit$git_status$git_metrics$fill{right}
[│](fg:muted) ${{custom.git_age}}${{custom.project_status}}{dev}{container}{cloud}
$character"""
right_format = ""

{_palette(colors)}
[fill]
symbol = "─"
style = "fg:muted"
[os]
disabled = {_bool(not p['os_enabled'])}
format = "[$symbol](bold fg:accent) "
{_os_symbols()}
[directory]
format = "[{p['path_icon']} $path](bold fg:fg) "
truncation_length = {int(p['path_length'])}
truncate_to_repo = {_bool(p['path_repo_root'])}
[git_branch]
disabled = {_bool(not p['branch_enabled'])}
symbol = "{p['branch_icon']} "
format = "[$symbol$branch(:$remote_branch)](bold fg:accent2) "
[git_commit]
commit_hash_length = 7
only_detached = false
tag_disabled = false
tag_symbol = " 󰓹 "
format = "[{_G['git_commit']} $hash$tag](fg:muted) "
{_git_status_block(p)}
[git_metrics]
disabled = false
only_nonzero_diffs = true
format = "([+$added](bold fg:success) )([-$deleted](bold fg:urgent) )"
[custom.git_age]
command = "git log -1 --format=%cr 2>/dev/null"
when = "git rev-parse --is-inside-work-tree >/dev/null 2>&1"
format = "[{_G['git_age']} $output](fg:muted) "
[custom.project_status]
command = 'root=$(git rev-parse --show-toplevel 2>/dev/null) || exit 1; cat "$root/.starship-status"'
when = 'root=$(git rev-parse --show-toplevel 2>/dev/null) && test -s "$root/.starship-status"'
format = "[{_G['project_status']} $output](bold fg:accent2) "
{_dev_modules()}
{_telemetry(p)}
[character]
success_symbol = "[╰─ {p['success_symbol']}](bold fg:accent)"
error_symbol = "[╰─ {p['error_symbol']}](bold fg:urgent)"
vimcmd_symbol = "[╰─ {p['vim_symbol']}](bold fg:accent2)"
'''


def render(colors: dict, settings: dict | None = None) -> str:
    """Render the selected Starship layout using the active desktop palette."""
    if settings is None:
        p = profile()
    else:
        p = dict(DEFAULT)
        for key, default in DEFAULT.items():
            value = settings.get(key, default)
            if type(value) is type(default):
                p[key] = value
        p["prompt_style"] = normalize_style(p.get("prompt_style"))
    style = normalize_style(p.get("prompt_style"))
    renderers = {
        "workspace": _workspace,
        "minimal": _minimal,
        "hud": _hud,
        "neon": _neon,
        "operator": _operator,
    }
    return renderers[style](p, colors)
