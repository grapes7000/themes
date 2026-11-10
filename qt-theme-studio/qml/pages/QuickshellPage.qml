import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts
import "../components"
import "../theme"

Item {
    id: root
    property var rows: JSON.parse(studioBridge.quickshellRowsJson)
    property var uiStyle: JSON.parse(studioBridge.uiStyleJson)
    property var motionRows: JSON.parse(studioBridge.quickshellMotionJson)
    property var roles: JSON.parse(studioBridge.roleNamesJson)
    property var palette: JSON.parse(studioBridge.paletteRowsJson)
    property bool advanced: false
    property string selectedColorRole: "accent"
    property bool sliderDragging: false
    property bool refreshPending: false
    property string inspectedPart: ""
    property var inspectedRoles: []
    readonly property string inspectedColors: inspectedPart ? inspectedPart + ": " + inspectedRoles.map(function(key) {
        const row = root.palette.find(item => item.key === key)
        return row ? row.label + " (" + key + "): " + row.value : key
    }).join("; ") : "Right-click the example to identify its colors."
    function refreshRows() {
        if (sliderDragging) { refreshPending = true; return }
        rows = JSON.parse(studioBridge.quickshellRowsJson)
        uiStyle = JSON.parse(studioBridge.uiStyleJson)
        motionRows = JSON.parse(studioBridge.quickshellMotionJson)
        palette = JSON.parse(studioBridge.paletteRowsJson)
        refreshPending = false
    }
    function styleValue(key, fallback) {
        const row = uiStyle.rows.find(row => row.key === key)
        return row ? row.value : fallback
    }
    function shellValue(key, fallback) {
        const row = rows.find(row => row.path === "components.homepage." + key)
        return row ? row.value : fallback
    }
    function roleColor(key, fallback) {
        if (key && key.charAt(0) === "#") return key
        const row = palette.find(row => row.key === key)
        return row && row.value ? row.value : fallback
    }
    function chooseColor(role) {
        selectedColorRole = role
        picker.selectedColor = roleColor(role, "#ffffff")
        picker.open()
    }
    Connections { target: studioBridge; function onStateChanged() { root.refreshRows() } }
    Component.onCompleted: refreshRows()
    ShellControlHelp { id: shellHelp }
    ColorDialog {
        id: picker
        title: "Choose a theme color"
        onAccepted: studioBridge.setRole(root.selectedColorRole, selectedColor.toString().toUpperCase())
    }

    ScrollView {
        anchors.fill: parent
        clip: true
        contentWidth: availableWidth
        ColumnLayout {
            width: parent.width
            spacing: Theme.spacingMedium
            Text { text: "Quickshell"; color: Theme.textPrimary; font.family: Theme.fontFamily; font.pixelSize: 28; font.weight: Font.Bold }
            Text { text: "Adjust the bar and drawers. The example below updates after each edit; hover over its buttons to see their outlines."; color: Theme.textSecondary; font.family: Theme.fontFamily; font.pixelSize: 13; wrapMode: Text.WordWrap; Layout.fillWidth: true }
            SectionCard {
                Layout.fillWidth: true
                title: "Shell example"
                subtitle: "Illustration of the bar and a drawer, not your exact widget layout. Hover a button to see the hover color."
                ShellPreview {
                    Layout.fillWidth: true
                    backgroundColor: root.roleColor("bg", "#181825")
                    barColor: root.roleColor(root.shellValue("bar_surface_role", "surface_0"), "#242433")
                    drawerColor: root.roleColor(root.shellValue("drawer_surface_role", "surface_1"), "#303040")
                    buttonColor: root.roleColor("surface_1", "#303040")
                    outlineColor: root.roleColor(root.shellValue("bar_outline_role", "border_subtle"), "#606070")
                    drawerOutlineColor: root.roleColor(root.shellValue("drawer_outline_role", "border_subtle"), "#606070")
                    accentColor: root.roleColor("accent", "#89b4fa")
                    textColor: root.roleColor("text", "#ffffff")
                    hoverColor: root.roleColor("hover", "#454557")
                    barOpacity: Number(root.shellValue("bar_opacity", 0.96))
                    drawerOpacity: Number(root.shellValue("drawer_opacity", 0.97))
                    outlineOpacity: Number(root.shellValue("bar_outline_opacity", 0.72))
                    drawerOutlineOpacity: Number(root.shellValue("drawer_outline_opacity", 0.76))
                    barRadius: Number(root.styleValue("radius_surface", 4))
                    buttonRadius: Number(root.styleValue("radius_control", 3))
                    drawerRadius: Number(root.styleValue("radius_overlay", 8))
                    drawerWidth: Number(root.shellValue("drawer_width", 420))
                    outlineWidth: Number(root.styleValue("border_width", 1))
                    quietButtons: root.styleValue("button", "quiet") === "quiet"
                    barRole: root.shellValue("bar_surface_role", "surface_0")
                    drawerRole: root.shellValue("drawer_surface_role", "surface_1")
                    barOutlineRole: root.shellValue("bar_outline_role", "border_subtle")
                    drawerOutlineRole: root.shellValue("drawer_outline_role", "border_subtle")
                    onInspected: function(part, roles) {
                        root.inspectedPart = part
                        root.inspectedRoles = roles
                    }
                }
                Text { objectName: "shell-color-inspection"; text: root.inspectedColors; color: Theme.textSecondary; wrapMode: Text.WordWrap; font.pixelSize: 11; Layout.fillWidth: true }
            }
            SectionCard {
                Layout.fillWidth: true
                title: "Colors and corners"
                subtitle: "Colors are shared theme colors, so changing one may also affect other parts of your desktop."
                Repeater {
                    model: [
                        { label: "Bar background", role: root.shellValue("bar_surface_role", "surface_0") },
                        { label: "Bar outline", role: root.shellValue("bar_outline_role", "border_subtle") },
                        { label: "Drawer background", role: root.shellValue("drawer_surface_role", "surface_1") },
                        { label: "Drawer outline", role: root.shellValue("drawer_outline_role", "border_subtle") },
                        { label: "Button hover outline (accent)", role: "accent" },
                        { label: "Button hover background", role: "hover" }
                    ]
                    delegate: RowLayout {
                        required property var modelData
                        Layout.fillWidth: true
                        Text { text: modelData.label; color: Theme.textSecondary; Layout.fillWidth: true }
                        Rectangle { width: 28; height: 28; radius: 4; color: root.roleColor(modelData.role, "#ffffff"); border.color: Theme.border }
                        SecondaryButton { text: "Choose color"; enabled: root.roles.indexOf(modelData.role) >= 0; onClicked: root.chooseColor(modelData.role) }
                    }
                }
                Repeater {
                    model: [
                        { key: "radius_control", label: "Button roundness" },
                        { key: "radius_surface", label: "Bar roundness" },
                        { key: "radius_overlay", label: "Drawer roundness" },
                        { key: "border_width", label: "Outline thickness" }
                    ]
                    delegate: RowLayout {
                        required property var modelData
                        Layout.fillWidth: true
                        Text { text: modelData.label; color: Theme.textSecondary; Layout.preferredWidth: 220 }
                        Slider {
                            id: simpleSlider
                            objectName: "shell-simple." + modelData.key
                            Layout.fillWidth: true
                            from: 0; to: modelData.key === "border_width" ? 10 : 60; stepSize: 1
                            snapMode: Slider.SnapAlways
                            value: Number(root.styleValue(modelData.key, 0))
                            Accessible.name: modelData.label
                            onMoved: if (!pressed) studioBridge.setUiStyleValue("metrics", modelData.key, String(Math.round(value)))
                            onPressedChanged: {
                                if (pressed) root.sliderDragging = true
                                else if (root.sliderDragging) {
                                    studioBridge.setUiStyleValue("metrics", modelData.key, String(Math.round(value)))
                                    root.sliderDragging = false
                                    if (root.refreshPending) root.refreshRows()
                                }
                            }
                        }
                        Text { text: Math.round(simpleSlider.value); color: Theme.textPrimary; Layout.preferredWidth: 60; horizontalAlignment: Text.AlignHCenter }
                    }
                }
            }
            SectionCard {
                Layout.fillWidth: true
                title: "Bar and drawer"
                subtitle: "Adjust how see-through the surfaces and outlines are, and how wide the drawer opens."
                Repeater {
                    model: root.rows.filter(row => ["bar_opacity", "bar_outline_opacity", "drawer_width", "drawer_opacity", "drawer_outline_opacity"].indexOf(row.path.split(".").pop()) >= 0)
                    delegate: RowLayout {
                        required property var modelData
                        Layout.fillWidth: true
                        Text { text: modelData.label; color: Theme.textSecondary; Layout.preferredWidth: 220 }
                        Slider {
                            id: surfaceSlider
                            objectName: "shell-simple." + modelData.path
                            Layout.fillWidth: true
                            from: modelData.minimum; to: modelData.maximum; stepSize: modelData.step
                            snapMode: Slider.SnapAlways
                            value: Number(modelData.value)
                            Accessible.name: modelData.label
                            onMoved: if (!pressed) studioBridge.setQuickshellValue(modelData.path, String(value))
                            onPressedChanged: {
                                if (pressed) root.sliderDragging = true
                                else if (root.sliderDragging) {
                                    studioBridge.setQuickshellValue(modelData.path, String(value))
                                    root.sliderDragging = false
                                    if (root.refreshPending) root.refreshRows()
                                }
                            }
                        }
                        Text { text: Number(surfaceSlider.value.toFixed(2)); color: Theme.textPrimary; Layout.preferredWidth: 60; horizontalAlignment: Text.AlignHCenter }
                    }
                }
            }
            CheckBox { objectName: "shell-advanced"; text: "Show advanced shell style settings"; checked: root.advanced; onToggled: root.advanced = checked }
            SectionCard {
                visible: root.advanced
                Layout.fillWidth: true
                title: "Shell shape and style"
                subtitle: root.uiStyle.source === "override" ? "A global style is active. Choose a style here or follow the theme to customize it." : "Choose a style, then adjust its sizes, corners, and patterns for this theme."
                SecondaryButton {
                    visible: root.uiStyle.source === "override"
                    text: "Follow this theme's style"
                    onClicked: studioBridge.followThemeUiStyle()
                }
                ThemedComboBox {
                    Layout.fillWidth: true
                    model: root.uiStyle.profiles
                    currentIndex: Math.max(0, root.uiStyle.profiles.indexOf(root.uiStyle.name))
                    onActivated: studioBridge.selectUiStyle(currentText)
                }
                Text { text: shellHelp.describeProfile(root.uiStyle.name); color: Theme.textMuted; font.pixelSize: 12; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                Repeater {
                    model: root.uiStyle.rows
                    delegate: ColumnLayout {
                        required property var modelData
                        Layout.fillWidth: true
                        spacing: 3
                        RowLayout {
                        Layout.fillWidth: true
                        Text { text: shellHelp.label(modelData.key, modelData.label); color: Theme.textSecondary; font.family: Theme.fontFamily; font.pixelSize: 13; Layout.preferredWidth: 220; wrapMode: Text.WordWrap }
                        Slider {
                            id: metricSlider
                            objectName: "ui-style." + modelData.key
                            visible: modelData.kind === "metric"
                            from: 0
                            to: modelData.maximum || 0
                            stepSize: 1
                            snapMode: Slider.SnapAlways
                            value: Number(modelData.value) || 0
                            Layout.fillWidth: true
                            Accessible.name: shellHelp.label(modelData.key, modelData.label)
                            onMoved: if (!pressed) studioBridge.setUiStyleValue("metrics", modelData.key, String(Math.round(value)))
                            onPressedChanged: {
                                if (pressed) root.sliderDragging = true
                                else if (root.sliderDragging) {
                                    studioBridge.setUiStyleValue("metrics", modelData.key, String(Math.round(value)))
                                    root.sliderDragging = false
                                    if (root.refreshPending) root.refreshRows()
                                }
                            }
                        }
                        Text { visible: modelData.kind === "metric"; text: metricSlider.pressed ? Math.round(metricSlider.value) : modelData.value; color: Theme.textPrimary; Layout.preferredWidth: 60; horizontalAlignment: Text.AlignHCenter }
                        ThemedComboBox {
                            visible: modelData.kind === "pattern"
                            Layout.fillWidth: true
                            model: modelData.choices || []
                            currentIndex: Math.max(0, model.indexOf(modelData.value))
                            onActivated: studioBridge.setUiStyleValue("patterns", modelData.key, currentText)
                        }
                        }
                        Text { text: shellHelp.describe(modelData.key); color: Theme.textMuted; font.pixelSize: 12; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                    }
                }
            }
            SectionCard {
                Layout.fillWidth: true
                visible: root.advanced
                title: "Shell motion"
                subtitle: "Adjust component transitions and button bounce. The motion pattern can turn them off."
                Repeater {
                    model: root.motionRows
                    delegate: ColumnLayout {
                        required property var modelData
                        Layout.fillWidth: true
                        spacing: 3
                        RowLayout {
                        Layout.fillWidth: true
                        Text { text: modelData.label; color: Theme.textSecondary; Layout.preferredWidth: 220 }
                        Slider {
                            id: motionSlider
                            objectName: "ui-style." + modelData.key
                            Layout.fillWidth: true
                            from: modelData.minimum
                            to: modelData.maximum
                            stepSize: 1
                            snapMode: Slider.SnapAlways
                            value: Number(modelData.value)
                            Accessible.name: modelData.label
                            onMoved: if (!pressed) studioBridge.setUiStyleValue("metrics", modelData.key, String(Math.round(value)))
                            onPressedChanged: {
                                if (pressed) root.sliderDragging = true
                                else if (root.sliderDragging) {
                                    studioBridge.setUiStyleValue("metrics", modelData.key, String(Math.round(value)))
                                    root.sliderDragging = false
                                    if (root.refreshPending) root.refreshRows()
                                }
                            }
                        }
                        Text { text: motionSlider.pressed ? Math.round(motionSlider.value) : modelData.value; color: Theme.textPrimary; Layout.preferredWidth: 60; horizontalAlignment: Text.AlignHCenter }
                        }
                        Text { text: shellHelp.describe(modelData.key); color: Theme.textMuted; font.pixelSize: 12; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                    }
                }
            }
            SectionCard {
                Layout.fillWidth: true
                visible: root.advanced
                title: "Live shell appearance"
                subtitle: "Quickshell watches theme changes, so committed edits update its surfaces without restarting the shell."
                Repeater {
                    model: root.rows
                    delegate: ColumnLayout {
                        required property var modelData
                        Layout.fillWidth: true
                        spacing: Theme.spacingSmall
                        RowLayout {
                        Layout.fillWidth: true
                        Text { text: modelData.label; color: Theme.textSecondary; font.family: Theme.fontFamily; font.pixelSize: 13; Layout.preferredWidth: 220; elide: Text.ElideRight }
                        ThemedComboBox {
                            visible: modelData.kind === "choice"
                            model: modelData.choices
                            currentIndex: Math.max(0, modelData.choices.indexOf(modelData.value))
                            Layout.fillWidth: true
                            onActivated: studioBridge.setQuickshellValue(modelData.path, currentText)
                        }
                        ThemedComboBox {
                            visible: modelData.kind === "role"
                            model: root.roles
                            currentIndex: Math.max(0, root.roles.indexOf(modelData.value))
                            Layout.fillWidth: true
                            onActivated: studioBridge.setQuickshellValue(modelData.path, currentText)
                        }
                        Slider {
                            id: shellSlider
                            objectName: modelData.path
                            visible: modelData.kind === "int" || modelData.kind === "float"
                            from: modelData.minimum
                            to: modelData.maximum
                            stepSize: modelData.step
                            snapMode: Slider.SnapAlways
                            value: Number(modelData.value)
                            Layout.fillWidth: true
                            Accessible.name: modelData.label
                            onMoved: if (!pressed) studioBridge.setQuickshellValue(modelData.path, String(value))
                            onPressedChanged: {
                                if (pressed) root.sliderDragging = true
                                else if (root.sliderDragging) {
                                    studioBridge.setQuickshellValue(modelData.path, String(value))
                                    root.sliderDragging = false
                                    if (root.refreshPending) root.refreshRows()
                                }
                            }
                        }
                        Text { visible: modelData.kind === "int" || modelData.kind === "float"; text: shellSlider.pressed ? Number(shellSlider.value.toFixed(3)) : modelData.value; color: Theme.textPrimary; Layout.preferredWidth: 60; horizontalAlignment: Text.AlignHCenter }
                        }
                        Text { text: shellHelp.describe(modelData.path.split(".").pop()) + (modelData.kind === "role" ? " " + shellHelp.describeRole(modelData.value) : ""); color: Theme.textMuted; font.pixelSize: 12; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                    }
                }
            }
        }
    }
}
