from __future__ import annotations

import json
import os
import tempfile

PROFILE_PATH = os.path.join(os.path.expanduser("~"), ".config", "theme-engine", "starship.json")

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
    "os_arch": chr(0xF0303),
    "os_debian": chr(0xF0306),
    "os_fedora": chr(0xF030A),
    "os_ubuntu": chr(0xF031B),
    "os_mint": chr(0xF030E),
    "os_linux": chr(0xF031A),
    "os_macos": chr(0xF0179),
    "os_windows": chr(0xF017A),
    "python": chr(0xE73C),
    "nodejs": chr(0xE718),
    "rust": chr(0xE7A8),
    "golang": chr(0xE627),
    "java": chr(0xE738),
    "lua": chr(0xE620),
    "php": chr(0xE73D),
    "ruby": chr(0xE739),
    "package": chr(0xF03D6),
    "docker": chr(0xF0868),
    "kubernetes": chr(0xF10FE),
    "terraform": chr(0xF1062),
    "nix": chr(0xF1105),
    "conda": chr(0xF0C3),
    "aws": chr(0xF0E0F),
    "azure": chr(0xF0805),
    "gcloud": chr(0xF11F6),
    "memory": chr(0xF035B),
    "time": chr(0xF017),
    "batt_full": chr(0xF0079),
    "batt_charge": chr(0xF0084),
    "batt_low": chr(0xF007B),
    "doc_ico": chr(0xF0219),
    "dl_ico": chr(0xF01DA),
    "pic_ico": chr(0xF02E9),
    "cfg_ico": chr(0xF0493),
}

STYLE_NAMES = ("workspace", "minimal", "hud", "neon", "operator")
STYLE_DESCRIPTIONS = {
    "workspace": "the original filled Powerline prompt, unchanged",
    "minimal": "quiet two-line directory + Git prompt",
    "hud": "dashboard with dynamic fill and right-side telemetry",
    "neon": "transparent SYS / PATH / GIT cyber layout",
    "operator": "multi-line repository console with cached project status",
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
    "lead_fade": "",
    "lead_arrow": "",
    "git_connector": "",
    "git_end": "",
    "path_end": "",
    "path_icon": _G["folder"],
    "path_length": 6,
    "path_repo_root": True,
    "os_enabled": True,
    "branch_enabled": True,
    "branch_icon": _G["git_branch"],
    "state_enabled": True,
    "state_icon": _G["git_state"],
    "status_enabled": True,
    "status_conflicted": _G["conflicted"],
    "status_ahead": _G["ahead"],
    "status_behind": _G["behind"],
    "status_diverged": _G["diverged"],
    "status_untracked": _G["untracked"],
    "status_stashed": _G["stashed"],
    "status_modified": _G["modified"],
    "status_staged": _G["staged"],
    "status_renamed": _G["renamed"],
    "status_deleted": _G["deleted"],
    "dev_enabled": True,
    "container_enabled": True,
    "cloud_enabled": True,
    "duration_enabled": True,
    "duration_icon": _G["cmd_duration"],
    "duration_min_ms": 2000,
    "cmd_status_enabled": True,
    "cmd_status_icon": _G["status_fail"],
    "jobs_enabled": True,
    "jobs_icon": _G["jobs"],
    "battery_enabled": True,
    "memory_enabled": True,
    "memory_threshold": 75,
    "time_enabled": True,
    "success_symbol": _G["arrow_ok"],
    "error_symbol": _G["arrow_ok"],
    "vim_symbol": _G["arrow_vim"],
}

STYLE_PRESETS = {
    "workspace": {
        "os_enabled": True,
        "dev_enabled": True,
        "container_enabled": True,
        "cloud_enabled": True,
        "duration_enabled": True,
        "cmd_status_enabled": True,
        "jobs_enabled": True,
        "battery_enabled": True,
        "memory_enabled": True,
        "time_enabled": True,
    },
    "minimal": {
        "os_enabled": False,
        "dev_enabled": False,
        "container_enabled": False,
        "cloud_enabled": False,
        "duration_enabled": True,
        "cmd_status_enabled": True,
        "jobs_enabled": False,
        "battery_enabled": False,
        "memory_enabled": False,
        "time_enabled": False,
    },
    "hud": {
        "os_enabled": True,
        "dev_enabled": True,
        "container_enabled": False,
        "cloud_enabled": False,
        "duration_enabled": True,
        "cmd_status_enabled": True,
        "jobs_enabled": True,
        "battery_enabled": True,
        "memory_enabled": False,
        "time_enabled": True,
    },
    "neon": {
        "os_enabled": True,
        "dev_enabled": True,
        "container_enabled": True,
        "cloud_enabled": False,
        "duration_enabled": True,
        "cmd_status_enabled": True,
        "jobs_enabled": True,
        "battery_enabled": True,
        "memory_enabled": False,
        "time_enabled": True,
    },
    "operator": {
        "os_enabled": True,
        "dev_enabled": True,
        "container_enabled": True,
        "cloud_enabled": True,
        "duration_enabled": True,
        "cmd_status_enabled": True,
        "jobs_enabled": True,
        "battery_enabled": True,
        "memory_enabled": False,
        "time_enabled": True,
    },
}


def normalize_style(value) -> str:
    raw = str(value or "").strip().lower()
    if raw in STYLE_NAMES:
        return raw
    return _STYLE_ALIASES.get(raw, "workspace")


def apply_style(values, style: str):
    name = normalize_style(style)
    out = dict(values)
    out["prompt_style"] = name
    out.update(STYLE_PRESETS[name])
    return out


def profile():
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
        if key == "prompt_style":
            values[key] = normalize_style(value)
        elif type(value) is type(default):
            values[key] = value
    return values


def save(values):
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


def _palette(colors):
    bg = colors["bg"]
    text = colors["text"]
    accent = colors.get("accent", text)
    return {
        "bg": bg,
        "surface": colors.get("bg_alt", bg),
        "fg": text,
        "muted": colors.get("text_dim", text),
        "accent": accent,
        "accent2": colors.get("accent2", accent),
        "urgent": colors.get("urgent", accent),
        "warn": colors.get("ansi_yellow", colors.get("warning", accent)),
        "success": colors.get("ansi_green", colors.get("success", colors.get("accent2", accent))),
    }


def _bool(value):
    return str(bool(value)).lower()


def _identity_block(p):
    return "$os$username$hostname" if p["os_enabled"] else "$username$hostname"


def _context_format(p):
    dev = "$python$nodejs$rust$golang$java$lua$php$ruby$package" if p["dev_enabled"] else ""
    container = "$docker_context$kubernetes" if p["container_enabled"] else ""
    cloud = "$terraform$nix_shell$conda$aws$gcloud$azure" if p["cloud_enabled"] else ""
    return dev + container + cloud


def _right_format(p, *, jobs=True, battery=True, time=True):
    return "".join([
        "$status" if p["cmd_status_enabled"] else "",
        "$cmd_duration" if p["duration_enabled"] else "",
        "$jobs" if jobs and p["jobs_enabled"] else "",
        "$battery" if battery and p["battery_enabled"] else "",
        "$time" if time and p["time_enabled"] else "",
    ])


def _header(style):
    return f'''# AUTO-GENERATED by `theme`
# STARSHIP_STYLE = {style}
"$schema" = 'https://starship.rs/config-schema.json'
add_newline = false
palette = "theme"
'''


def _palette_block(p):
    return f'''
[palettes.theme]
bg = "{p['bg']}"
surface = "{p['surface']}"
fg = "{p['fg']}"
muted = "{p['muted']}"
accent = "{p['accent']}"
accent2 = "{p['accent2']}"
urgent = "{p['urgent']}"
warn = "{p['warn']}"
success = "{p['success']}"
'''


def _os_config(workspace=False):
    if workspace:
        os_format = "[ $symbol]($style)"
        os_style = "bold fg:accent bg:surface"
        user_style = "bold fg:fg bg:surface"
        root_style = "bold fg:urgent bg:surface"
        host_style = "bold fg:accent2 bg:surface"
    else:
        os_format = "[$symbol]($style)"
        os_style = "bold fg:accent"
        user_style = "bold fg:fg"
        root_style = "bold fg:urgent"
        host_style = "bold fg:accent2"
    return f'''
[os]
disabled = false
format = "{os_format}"
style = "{os_style}"

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
style_user = "{user_style}"
style_root = "{root_style}"
show_always = false

[hostname]
ssh_only = true
trim_at = "."
format = "[@$hostname ]($style)"
style = "{host_style}"
'''


def _directory_config(p, style):
    if style == "workspace":
        fmt = f"[ {p['path_icon']} $path ]($style)"
        sty = "bold fg:bg bg:accent"
    elif style == "minimal":
        fmt = f"[{p['path_icon']} $path]($style)"
        sty = "bold fg:accent"
    elif style == "hud":
        fmt = f"[{p['path_icon']} $path]($style)"
        sty = "bold fg:fg"
    elif style == "neon":
        fmt = f"[{p['path_icon']} $path]($style)"
        sty = "bold fg:accent2"
    else:
        fmt = f"[{p['path_icon']} $path]($style)"
        sty = "bold fg:fg"
    return f'''
[directory]
format = "{fmt}"
style = "{sty}"
truncation_length = {int(p['path_length'])}
truncate_to_repo = {_bool(p['path_repo_root'])}

[directory.substitutions]
"Documents" = "{_G['doc_ico']} Documents"
"Downloads" = "{_G['dl_ico']} Downloads"
"Pictures" = "{_G['pic_ico']} Pictures"
".config" = "{_G['cfg_ico']} .config"
'''


def _legacy_git_config(p):
    return f'''
[git_branch]
disabled = {_bool(not p['branch_enabled'])}
symbol = "{p['branch_icon']} "
format = "[$symbol$branch(:$remote_branch) ]($style)"
style = "bold fg:bg bg:accent2"

[git_state]
disabled = {_bool(not p['state_enabled'])}
format = "[{p['state_icon']} $state( $progress_current/$progress_total) ]($style)"
style = "bold fg:urgent bg:accent2"

[git_status]
disabled = {_bool(not p['status_enabled'])}
format = "([$all_status$ahead_behind]($style))"
style = "bold fg:bg bg:accent2"
conflicted = "[{p['status_conflicted']} ${{count}}](bold fg:bg bg:urgent) "
ahead = "{p['status_ahead']}${{count}} "
behind = "{p['status_behind']}${{count}} "
diverged = "{p['status_diverged']}⇡${{ahead_count}}⇣${{behind_count}} "
untracked = "{p['status_untracked']}${{count}} "
stashed = "{p['status_stashed']}${{count}} "
modified = "{p['status_modified']}${{count}} "
staged = "{p['status_staged']}${{count}} "
renamed = "{p['status_renamed']}${{count}} "
deleted = "[{p['status_deleted']}${{count}}](bold fg:bg bg:urgent) "
'''


def _rich_git_config(p, style):
    colors = {
        "minimal": ("accent2", "muted", "urgent", "muted", "muted"),
        "hud": ("accent2", "muted", "urgent", "accent", "muted"),
        "neon": ("accent", "accent2", "urgent", "fg", "muted"),
        "operator": ("accent", "accent2", "urgent", "fg", "muted"),
    }
    branch_c, commit_c, state_c, status_c, metrics_c = colors[style]
    commit_fmt = "" if style == "minimal" else f"[ {_G['git_commit']} $hash$tag](fg:{commit_c})"
    metrics_fmt = "" if style == "minimal" else f"[ +$added/-$deleted](fg:{metrics_c})"
    remote = "" if style in {"minimal", "hud", "neon"} else "(:$remote_branch)"
    return f'''
[git_branch]
disabled = {_bool(not p['branch_enabled'])}
symbol = "{p['branch_icon']} "
format = "[$symbol$branch{remote}](bold fg:{branch_c})"

[git_commit]
disabled = false
only_detached = false
tag_disabled = false
tag_symbol = " 󰓹 "
commit_hash_length = 7
format = "{commit_fmt}"

[git_state]
disabled = {_bool(not p['state_enabled'])}
format = "[ {p['state_icon']} $state( $progress_current/$progress_total)](bold fg:{state_c})"

[git_status]
disabled = {_bool(not p['status_enabled'])}
format = "([$all_status$ahead_behind](bold fg:{status_c}))"
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
format = "{metrics_fmt}"
'''


def _context_config():
    rows = [
        ("python", _G["python"], "$version", "accent2"),
        ("nodejs", _G["nodejs"], "$version", "accent2"),
        ("rust", _G["rust"], "$version", "accent2"),
        ("golang", _G["golang"], "$version", "accent2"),
        ("java", _G["java"], "$version", "accent2"),
        ("lua", _G["lua"], "$version", "accent2"),
        ("php", _G["php"], "$version", "accent2"),
        ("ruby", _G["ruby"], "$version", "accent2"),
        ("package", _G["package"], "$version", "muted"),
        ("docker_context", _G["docker"], "$context", "muted"),
        ("terraform", _G["terraform"], "$workspace", "muted"),
        ("nix_shell", _G["nix"], "$state", "muted"),
        ("conda", _G["conda"], "$environment", "muted"),
        ("aws", _G["aws"], "$profile", "accent"),
        ("gcloud", _G["gcloud"], "$account", "accent"),
        ("azure", _G["azure"], "$subscription", "accent"),
    ]
    out = []
    for name, symbol, value, color in rows:
        extra = "\nignore_base = true" if name == "conda" else "\ndisabled = false" if name == "azure" else ""
        out.append(f'''\n[{name}]\nsymbol = "{symbol} "\nformat = "[$symbol{value} ](bold fg:{color})"{extra}\n''')
    out.append(f'''
[kubernetes]
disabled = false
symbol = "{_G['kubernetes']} "
format = '[$symbol$context( \($namespace\)) ](bold fg:accent2)'
detect_files = ["Chart.yaml", "kustomization.yaml", "skaffold.yaml"]
detect_folders = [".kube", "k8s"]
''')
    return "".join(out)


def _telemetry_config(p):
    return f'''
[memory_usage]
disabled = {_bool(not p['memory_enabled'])}
threshold = {int(p['memory_threshold'])}
symbol = "{_G['memory']} "
format = "[$symbol$ram ](bold fg:urgent)"

[cmd_duration]
disabled = {_bool(not p['duration_enabled'])}
min_time = {int(p['duration_min_ms'])}
format = "[ {p['duration_icon']} $duration ](bold fg:fg)"

[status]
disabled = {_bool(not p['cmd_status_enabled'])}
success_symbol = ""
format = "[ {p['cmd_status_icon']} $status ](bold fg:urgent)"

[jobs]
disabled = {_bool(not p['jobs_enabled'])}
symbol = "{p['jobs_icon']} "
format = "[$symbol$number ](bold fg:accent)"

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
format = "[$symbol$percentage]($style)"

[time]
disabled = {_bool(not p['time_enabled'])}
time_format = "%I:%M %p"
format = "[ {_G['time']} $time ](bold fg:warn)"
'''


def _character_config(p, compact=False):
    prefix = "" if compact else "╰─ "
    return f'''
[character]
success_symbol = "[{prefix}{p['success_symbol']}](bold fg:accent)"
error_symbol = "[{prefix}{p['error_symbol']}](bold fg:urgent)"
vimcmd_symbol = "[{prefix}{p['vim_symbol']}](bold fg:accent2)"
vimcmd_replace_one_symbol = "[{prefix}{p['vim_symbol']}](bold fg:urgent)"
vimcmd_replace_symbol = "[{prefix}{p['vim_symbol']}](bold fg:urgent)"
vimcmd_visual_symbol = "[{prefix}{p['vim_symbol']}](bold fg:accent2)"
'''


def _render_workspace(p, palette):
    # Preserve the pre-switcher workspace exactly in visible geometry and
    # module ordering. This is the known-good prompt the style system started from.
    git = ("$git_branch" if p["branch_enabled"] else "") + ("$git_state" if p["state_enabled"] else "") + ("$git_status" if p["status_enabled"] else "")
    git_custom = ""
    if git:
        git = f"${{custom.git_connector}}{git}${{custom.git_end}}"
        git_custom = f'''
[custom.git_connector]
command = "printf x"
when = "git rev-parse --is-inside-work-tree >/dev/null 2>&1"
format = "[{p['git_connector']}](fg:accent bg:accent2)"

[custom.git_end]
command = "printf x"
when = "git rev-parse --is-inside-work-tree >/dev/null 2>&1"
format = "[{p['git_end']}](fg:accent2)"
'''
    identity = _identity_block(p)
    context = _context_format(p)
    right = _right_format(p)
    right_format = f"({right})" if right else ""
    return _header("workspace") + f'''
format = """
[{p['lead_fade']}](fg:surface){identity}[ ](bg:surface)[{p['lead_arrow']}](fg:surface bg:accent)\
$directory\
{git}${{custom.path_end}}\
{context}$memory_usage\
$line_break$character"""

right_format = """{right_format}"""
{git_custom}
[custom.path_end]
command = "printf x"
when = "! git rev-parse --is-inside-work-tree >/dev/null 2>&1"
format = "[{p['path_end']}](fg:accent)"
''' + _palette_block(palette) + _os_config(workspace=True) + _directory_config(p, "workspace") + _legacy_git_config(p) + _context_config() + _telemetry_config(p) + _character_config(p)


def _render_minimal(p, palette):
    right = "".join(["$status" if p["cmd_status_enabled"] else "", "$cmd_duration" if p["duration_enabled"] else ""])
    return _header("minimal") + f'''
format = """$directory[  ](fg:muted)$git_branch$git_state$git_status$line_break$character"""
right_format = """{right}"""
''' + _palette_block(palette) + _os_config() + _directory_config(p, "minimal") + _rich_git_config(p, "minimal") + _context_config() + _telemetry_config(p) + _character_config(p, compact=True)


def _render_hud(p, palette):
    identity = "$os" if p["os_enabled"] else ""
    context = _context_format(p)
    alerts = _right_format(p, jobs=False, battery=False, time=False)
    telemetry = "".join(["$jobs" if p["jobs_enabled"] else "", "$battery" if p["battery_enabled"] else "", "$time" if p["time_enabled"] else ""])
    return _header("hud") + f'''
format = """[╭─](bold fg:accent){identity}$directory[  ](fg:muted)$git_branch$git_status$git_metrics{context}$fill{telemetry}[─╮](bold fg:accent)$line_break[╰─](bold fg:accent2)$character"""
right_format = """{alerts}"""

[fill]
symbol = "·"
style = "fg:muted"
''' + _palette_block(palette) + _os_config() + _directory_config(p, "hud") + _rich_git_config(p, "hud") + _context_config() + _telemetry_config(p) + _character_config(p, compact=True)


def _render_neon(p, palette):
    identity = _identity_block(p)
    context = _context_format(p)
    return _header("neon") + f'''
format = """
[◢ SYS ](bold fg:accent){identity}[  ](fg:muted)[PATH ](bold fg:accent2)$directory[  ](fg:muted)[GIT ](bold fg:accent)$git_branch$git_commit$git_state$git_status$git_metrics[ ◣](bold fg:accent)\
$line_break[└─ ENV ](fg:muted){context}$character"""
right_format = """{_right_format(p)}"""
''' + _palette_block(palette) + _os_config() + _directory_config(p, "neon") + _rich_git_config(p, "neon") + _context_config() + _telemetry_config(p) + _character_config(p, compact=True)


def _render_operator(p, palette):
    identity = _identity_block(p)
    context = _context_format(p)
    top_right = "".join(["$battery" if p["battery_enabled"] else "", "$time" if p["time_enabled"] else ""])
    alerts = _right_format(p, jobs=True, battery=False, time=False)
    return _header("operator") + f'''
format = """
[╭─ OPERATOR ](bold fg:accent){identity}$fill{top_right}\
$line_break[├─ cwd  ](bold fg:muted)$directory\
$line_break[├─ git  ](bold fg:muted)$git_branch$git_commit$git_state$git_status$git_metrics${{custom.git_age}}\
$line_break[├─ env  ](bold fg:muted){context}${{custom.project_status}}\
$line_break[╰─](bold fg:accent)$character"""
right_format = """{alerts}"""

[fill]
symbol = "─"
style = "fg:muted"

[custom.git_age]
command = 'git log -1 --format=%cr 2>/dev/null'
when = 'git rev-parse --is-inside-work-tree >/dev/null 2>&1'
format = "[ {_G['git_age']} $output](fg:muted)"

[custom.project_status]
command = 'root=$(git rev-parse --show-toplevel 2>/dev/null) || exit 1; head -n 1 "$root/.starship-status" 2>/dev/null'
when = 'root=$(git rev-parse --show-toplevel 2>/dev/null) || exit 1; test -s "$root/.starship-status"'
format = "[  {_G['project_status']} $output](bold fg:success)"
''' + _palette_block(palette) + _os_config() + _directory_config(p, "operator") + _rich_git_config(p, "operator") + _context_config() + _telemetry_config(p) + _character_config(p, compact=True)


def render(colors, settings=None):
    p = profile() if settings is None else dict(settings)
    style = normalize_style(p.get("prompt_style"))
    p["prompt_style"] = style
    palette = _palette(colors)
    renderers = {
        "workspace": _render_workspace,
        "minimal": _render_minimal,
        "hud": _render_hud,
        "neon": _render_neon,
        "operator": _render_operator,
    }
    return renderers[style](p, palette)
