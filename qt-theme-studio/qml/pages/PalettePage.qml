import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts
import QtQuick.Window
import "../components"
import "../theme"

Item {
    id: root
    property var paletteRows: JSON.parse(studioBridge.paletteRowsJson)
    property string colorRole: ""
    property color colorValue: "#000000"
    function refreshPalette() { root.paletteRows = JSON.parse(studioBridge.paletteRowsJson) }
    function openColorPicker(role, value) {
        root.colorRole = role; root.colorValue = value; picker.currentColor = value; picker.open()
    }
    function startEyedropper(role) {
        root.colorRole = role
        if (studioBridge.captureScreenForEyedropper() !== "") {
            eyedropperWindow.visibility = Window.FullScreen
            eyedropperWindow.visible = true
            eyedropperWindow.requestActivate()
        }
    }

    Connections { target: studioBridge; function onStateChanged() { root.refreshPalette() } }
    ColorDialog {
        id: picker
        title: "Choose " + root.colorRole
        selectedColor: root.colorValue
        onAccepted: studioBridge.setRole(root.colorRole, selectedColor.toString().toUpperCase())
    }
    Window {
        id: eyedropperWindow
        visible: false
        color: "black"
        flags: Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
        title: "Theme Studio eyedropper"
        Image {
            id: eyedropperImage
            anchors.fill: parent
            source: studioBridge.eyedropperImageUrl
            fillMode: Image.Stretch
            cache: false
        }
        MouseArea {
            anchors.fill: parent
            cursorShape: Qt.CrossCursor
            onClicked: function(mouse) {
                const color = studioBridge.screenColorAt(mouse.x, mouse.y, width, height)
                if (color !== "") studioBridge.setRole(root.colorRole, color)
                eyedropperWindow.visible = false
            }
        }
        Rectangle {
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.top: parent.top
            anchors.topMargin: 20
            color: Theme.surface
            border.color: Theme.accent
            radius: Theme.radiusSmall
            width: hint.implicitWidth + 28
            height: hint.implicitHeight + 16
            Text { id: hint; anchors.centerIn: parent; text: "Click a pixel to use it for " + root.colorRole + " · Esc cancels"; color: Theme.textPrimary; font.family: Theme.fontFamily }
        }
        Shortcut { sequence: "Esc"; onActivated: eyedropperWindow.visible = false }
    }
    FileDialog {
        id: paletteImporter
        title: "Import palette"
        nameFilters: ["Palette JSON (*.json)", "All files (*)"]
        fileMode: FileDialog.OpenFile
        onAccepted: studioBridge.importPalette(selectedFile)
    }
    FileDialog {
        id: paletteExporter
        title: "Export palette"
        nameFilters: ["Palette JSON (*.json)"]
        fileMode: FileDialog.SaveFile
        defaultSuffix: "json"
        onAccepted: studioBridge.exportPalette(selectedFile)
    }
    Dialog {
        id: newThemeDialog
        title: "Create a custom theme"
        modal: true
        anchors.centerIn: Overlay.overlay
        width: 430
        standardButtons: Dialog.Ok | Dialog.Cancel
        onAccepted: studioBridge.createTheme(themeName.text, seedField.text, darkToggle.checked)
        background: Rectangle { color: Theme.surface; border.color: Theme.border; radius: Theme.radiusMedium }
        contentItem: ColumnLayout {
            spacing: Theme.spacingMedium
            Text { text: "Start with a seed color; Theme Studio derives every semantic role. You can fine-tune them below afterwards."; color: Theme.textSecondary; wrapMode: Text.WordWrap; Layout.fillWidth: true }
            TextField {
                id: themeName; placeholderText: "Theme name"; selectByMouse: true; Layout.fillWidth: true; color: Theme.textPrimary
                background: Rectangle { color: Theme.bgElevated; border.color: parent.activeFocus ? Theme.focusRing : Theme.border; radius: Theme.radiusSmall }
            }
            RowLayout {
                Layout.fillWidth: true
                TextField {
                    id: seedField; text: "#8B7CF8"; placeholderText: "#RRGGBB"; selectByMouse: true; Layout.fillWidth: true; color: Theme.textPrimary
                    background: Rectangle { color: Theme.bgElevated; border.color: parent.activeFocus ? Theme.focusRing : Theme.border; radius: Theme.radiusSmall }
                }
                Rectangle { width: 32; height: 32; radius: Theme.radiusSmall; color: seedField.text; border.color: Theme.borderStrong }
            }
            RowLayout {
                Text { text: "Dark theme"; color: Theme.textPrimary; Layout.fillWidth: true }
                Switch { id: darkToggle; checked: true }
            }
        }
    }

    ScrollView {
        anchors.fill: parent
        clip: true
        contentWidth: availableWidth
        ColumnLayout {
            width: parent.width
            spacing: Theme.spacingMedium
            RowLayout {
                Layout.fillWidth: true
                Text { text: "Palette Studio"; color: Theme.textPrimary; font.family: Theme.fontFamily; font.pixelSize: 28; font.weight: Font.Bold }
                Item { Layout.fillWidth: true }
                SecondaryButton { text: "Import"; onClicked: paletteImporter.open() }
                SecondaryButton { text: "Export"; onClicked: paletteExporter.open() }
                PrimaryButton { text: "New custom theme"; onClicked: newThemeDialog.open() }
            }
            Text { text: "Every edit is part of the current Theme Studio draft: undo, recovery, live preview, and Save & Apply work exactly as they do elsewhere."; color: Theme.textSecondary; font.family: Theme.fontFamily; font.pixelSize: 13; wrapMode: Text.WordWrap; Layout.fillWidth: true }

            SectionCard {
                Layout.fillWidth: true
                title: "Generate a coherent palette"
                subtitle: "Generate all semantic roles from one seed color, or from the wallpaper selected on the Wallpapers page."
                RowLayout {
                    Layout.fillWidth: true
                    TextField {
                        id: generationSeed; text: "#8B7CF8"; placeholderText: "#RRGGBB"; selectByMouse: true; Layout.fillWidth: true; color: Theme.textPrimary
                        background: Rectangle { color: Theme.bgElevated; border.color: parent.activeFocus ? Theme.focusRing : Theme.border; radius: Theme.radiusSmall }
                    }
                    Rectangle { width: 32; height: 32; radius: Theme.radiusSmall; color: generationSeed.text; border.color: Theme.borderStrong }
                    Switch { id: generationDark; checked: studioBridge.dark }
                    Text { text: generationDark.checked ? "Dark" : "Light"; color: Theme.textSecondary }
                    SecondaryButton { text: "Generate from seed"; onClicked: studioBridge.generatePalette(generationSeed.text, generationDark.checked) }
                }
                RowLayout {
                    Layout.fillWidth: true
                    SecondaryButton { text: "Generate from selected wallpaper"; Layout.fillWidth: true; onClicked: studioBridge.generatePaletteFromSelectedWallpaper() }
                    Text { text: "Choose its image in Wallpapers first."; color: Theme.textMuted; font.pixelSize: 11 }
                }
            }

            SectionCard {
                Layout.fillWidth: true
                title: "Theme mode"
                subtitle: "Used by applications that adapt their rendering to light or dark palettes."
                RowLayout {
                    Layout.fillWidth: true
                    Text { text: "Dark theme"; color: Theme.textPrimary; Layout.fillWidth: true }
                    Switch { checked: studioBridge.dark; onToggled: studioBridge.setDark(checked) }
                }
            }

            SectionCard {
                Layout.fillWidth: true
                title: "Semantic colors"
                subtitle: "Click a swatch or Pick to open the platform color selector. If your system color dialog offers an eyedropper, use it to sample anywhere on screen."
                Repeater {
                    model: root.paletteRows
                    delegate: RowLayout {
                        required property var modelData
                        Layout.fillWidth: true
                        spacing: Theme.spacingSmall
                        Text { text: modelData.label; color: Theme.textSecondary; font.family: Theme.fontFamily; font.pixelSize: 13; Layout.preferredWidth: 180; elide: Text.ElideRight }
                        Rectangle {
                            width: 34; height: 30; radius: Theme.radiusSmall; color: modelData.value || "transparent"; border.color: Theme.borderStrong
                            MouseArea { anchors.fill: parent; onClicked: root.openColorPicker(modelData.key, modelData.value) }
                        }
                        TextField {
                            text: modelData.value; selectByMouse: true; Layout.preferredWidth: 112; color: Theme.textPrimary; font.family: Theme.fontFamily
                            background: Rectangle { color: Theme.bgElevated; border.color: parent.activeFocus ? Theme.focusRing : Theme.border; radius: Theme.radiusSmall }
                            onEditingFinished: studioBridge.setRole(modelData.key, text)
                        }
                        SecondaryButton { text: "Pick"; onClicked: root.openColorPicker(modelData.key, modelData.value) }
                        SecondaryButton { text: "Eyedropper"; onClicked: root.startEyedropper(modelData.key) }
                        Text {
                            text: modelData.key === "bg" ? "base" : (modelData.contrast >= 4.5 ? modelData.contrast + ":1" : "low " + modelData.contrast + ":1")
                            color: modelData.key === "bg" || modelData.contrast >= 4.5 ? Theme.success : Theme.warn
                            font.family: Theme.fontFamily; font.pixelSize: 11; Layout.fillWidth: true
                        }
                    }
                }
            }
        }
    }
}
