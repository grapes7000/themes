import QtQml

QtObject {
    readonly property var descriptions: ({
        grid: "A basic spacing unit in logical pixels. For example, it changes the distance drawers move during opening and some launcher gaps.",
        spacing_xs: "Extra-small spacing: the gap between the bar and the screen's top and sides, space between bar widgets, and small gaps inside widgets and menus.",
        spacing_sm: "Small spacing: padding inside bar buttons, the distance between the bar and drawers, and gaps in menus and panels.",
        spacing_md: "Medium spacing: padding inside drawers and menus, and space between panel contents.",
        spacing_lg: "Large spacing: larger gaps between sections, such as in the weather panel and launcher.",
        spacing_xl: "Extra-large spacing used in parts of the network and battery panels.",
        spacing_2xl: "Larger padding and spacing in panels, including Bluetooth, notifications and the menu.",
        spacing_3xl: "Very large spacing used in the application launcher.",
        page_padding: "Not currently used by the Arch-WM Quickshell; other applications may use this style value.",
        page_padding_compact: "Not currently used by the Arch-WM Quickshell; other applications may use this style value.",
        section_gap: "Not currently used by the Arch-WM Quickshell; other applications may use this style value.",
        sidebar_width: "Not currently used by the Arch-WM Quickshell; other applications may use this style value.",
        control_height_compact: "Height of compact controls, including workspace buttons and some panel rows.",
        control_height: "Height of standard controls, including menu rows and some panel buttons.",
        control_height_large: "Height of the bar and larger controls, including launcher and panel buttons.",
        icon_size: "Size of shell icons, including icons in the bar and panels.",
        icon_box: "Size of the space reserved for icons, including tray icons and bar buttons.",
        radius_control: "Roundness of buttons and other small controls.",
        radius_surface: "Roundness of the bar and some cards and list rows.",
        radius_overlay: "Roundness of drawers and launcher overlays.",
        border_width: "Thickness of outlines on the bar, drawers, buttons and other shell elements.",
        focus_width: "Thickness of the focus indicator in the application launcher.",
        font_caption: "Size of small labels, including text in the bar and tray menus.",
        font_secondary: "Size of secondary text, such as details in panels and menus.",
        font_body: "Size of ordinary text in widgets, menus and panels.",
        font_section: "Size of section headings in panels and widgets.",
        font_title: "Size of larger titles in menus and panels.",
        surface: "Flat uses subtler fills and outlines, for example in the tray menu and Bluetooth list. Card and bevel both use the stronger non-flat treatment in the current shell.",
        section: "Divider, group and card are section-layout styles. They are not currently used by the Arch-WM Quickshell, so changing this may have no visible shell effect.",
        list_row: "Flat makes launcher result rows square. Card rounds those rows using the surface corner setting.",
        selection: "Accent-soft-marker adds a colored marker beside the selected launcher result. Filled and solid-accent do not show that marker in the current shell.",
        button: "Quiet makes bar buttons mostly transparent until hovered, with a subtle hover outline. Filled and bevel use a visible background and stronger outline; the launcher also animates differently.",
        field: "Outlined, sunken and filled-outlined describe text-field styles. They are not currently used by the Arch-WM Quickshell, so changing this may have no visible shell effect.",
        dialog: "Elevated, framed and rounded-card describe dialog styles. They are not currently used by the Arch-WM Quickshell, so changing this may have no visible shell effect.",
        status: "Semantic-muted uses softer status colors, for example on an on/off status pill. Semantic-direct uses stronger colors.",
        shadow: "Overlay-only enables the shell's overlay shadow flag. Soft and hard do not enable that flag in the current shell.",
        motion: "None turns motion off. Restrained uses smaller, calmer transitions. Playful adds more movement and bounce, for example when opening a drawer or releasing a button.",
        motion_fast_ms: "Time in milliseconds for quick transitions, such as bar-button hover and press effects. Larger is slower.",
        motion_normal_ms: "Time in milliseconds for longer transitions, including button release animations. Larger is slower.",
        motion_hover_percent: "How much workspace buttons grow on hover; 100 means no growth.",
        motion_press_percent: "How much supported buttons shrink when pressed; 100 means no shrink.",
        motion_overshoot_percent: "How much supported buttons bounce when released. This is visible with the playful motion style.",
        bar_position: "Places the bar at the top or bottom of the screen.",
        bar_surface_role: "Chooses which shared palette color paints the bar background. For example, base surface is normally a dark background; accent is the theme's highlight color.",
        bar_opacity: "How opaque the bar background is: 0 is transparent, 1 is solid.",
        bar_outline_role: "Chooses the theme palette color used for the bar outline.",
        bar_outline_opacity: "How opaque the bar outline is: 0 is invisible, 1 is solid.",
        drawer_width: "Width of the shell drawers, in logical pixels.",
        drawer_surface_role: "Chooses which shared palette color paints drawer backgrounds. For example, raised surface 1 is normally slightly lighter than the base surface.",
        drawer_opacity: "How opaque drawer backgrounds are: 0 is transparent, 1 is solid.",
        drawer_outline_role: "Chooses the theme palette color used for drawer outlines.",
        drawer_outline_opacity: "How opaque drawer outlines are: 0 is invisible, 1 is solid.",
        card_opacity: "How opaque homepage cards are: 0 is transparent, 1 is solid.",
        image_fit: "How homepage images fit: cover fills and may crop; contain shows the whole image; fill stretches; fit uses the shell's fitted mode.",
        slideshow_seconds: "How many seconds each homepage slideshow image stays visible.",
        image_overlay_opacity: "Strength of the color overlay on homepage images.",
        image_dimming: "How much homepage images are darkened.",
        transition_ms: "Duration of homepage transitions in milliseconds. Larger is slower."
    })

    readonly property var labels: ({
        spacing_xs: "Extra-small spacing (XS)", spacing_sm: "Small spacing (SM)",
        spacing_md: "Medium spacing (MD)", spacing_lg: "Large spacing (LG)",
        spacing_xl: "Extra-large spacing (XL)", spacing_2xl: "Double extra-large spacing (2XL)",
        spacing_3xl: "Triple extra-large spacing (3XL)", radius_control: "Button corners",
        radius_surface: "Bar and card corners", radius_overlay: "Drawer corners",
        surface: "Surface style", section: "Section style", list_row: "List-row style",
        selection: "Selection style", button: "Button style", field: "Text-field style",
        dialog: "Dialog style", status: "Status colors", shadow: "Shadow style", motion: "Motion style"
    })

    readonly property var roleExamples: ({
        bg: "main desktop background", bg_alt: "alternate or raised background",
        text: "main text color", text_dim: "softer secondary text color",
        accent: "main highlight color, also used for bar-button hover outlines",
        accent2: "second highlight color", urgent: "urgent or error color",
        focus: "keyboard-focus highlight", border_normal: "normal window border",
        surface_0: "base background surface", surface_1: "first raised background surface",
        surface_2: "second raised background surface", overlay: "overlay background",
        hover: "background when the pointer is over an item", selected: "selected-item color",
        border_subtle: "subtle outline color", border_strong: "stronger outline color",
        success: "success state color", warning: "warning state color", info: "information state color",
        disabled: "disabled-item color", shadow: "shadow color", on_accent: "text color on an accent background",
        on_urgent: "text color on an urgent background"
    })

    readonly property var profiles: ({
        precision: "Compact and flat, with thin outlines and subtle motion.",
        atelier: "Clean, restrained controls and subtle motion.",
        legacy: "Roomier controls with rounder, filled styling and playful motion.",
        win95: "Compact retro styling with Windows 95-inspired controls and no motion."
    })

    function describe(key) {
        return descriptions[key] || "No description is available for this custom style setting."
    }
    function label(key, fallback) { return labels[key] || fallback }
    function describeRole(role) {
        return roleExamples[role] ? "Selected palette color: " + roleExamples[role] + "." : "This is a custom palette color."
    }
    function describeProfile(name) { return profiles[name] || "This is a custom style profile." }
}
