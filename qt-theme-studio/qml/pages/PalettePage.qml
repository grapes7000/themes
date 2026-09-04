import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../components"
import "../theme"

Item {
    ScrollView {
        anchors.fill: parent
        clip: true
        contentWidth: availableWidth
        ColumnLayout {
            width: parent.width
            spacing: 14
            Text { text: "Palette"; color: Theme.textPrimary; font.family: Theme.fontFamily; font.pixelSize: 28; font.weight: Font.Bold }
            Text { text: "Edit the core semantic colors. Enter #RRGGBB values; changes go through ThemeEditor and participate in undo, recovery, validation, and live preview."; color: Theme.textSecondary; font.family: Theme.fontFamily; font.pixelSize: 13; wrapMode: Text.WordWrap; Layout.fillWidth: true }
            SectionCard {
                Layout.fillWidth: true
                title: "Mode"
                subtitle: "This is theme metadata; the generated contract uses it for light/dark-aware consumers."
                RowLayout {
                    Layout.fillWidth: true
                    Text { text: "Dark theme"; color: Theme.textPrimary; font.family: Theme.fontFamily; Layout.fillWidth: true }
                    Switch { checked: studioBridge.dark; onToggled: studioBridge.setDark(checked) }
                }
            }
            SectionCard {
                Layout.fillWidth: true
                title: "Core roles"
                Repeater {
                    model: JSON.parse(studioBridge.roleRowsJson)
                    delegate: RowLayout {
                        required property var modelData
                        Layout.fillWidth: true
                        spacing: 12
                        Text { text: modelData.label; color: Theme.textSecondary; font.family: Theme.fontFamily; font.pixelSize: 13; Layout.preferredWidth: 180 }
                        Rectangle { width: 28; height: 28; radius: 6; color: modelData.value || "transparent"; border.color: Theme.borderStrong }
                        TextField {
                            Layout.fillWidth: true
                            text: modelData.value
                            selectByMouse: true
                            font.family: Theme.fontFamily
                            color: Theme.textPrimary
                            placeholderText: "#RRGGBB"
                            background: Rectangle { color: Theme.bgElevated; border.color: parent.activeFocus ? Theme.focusRing : Theme.border; radius: Theme.radiusSmall }
                            onEditingFinished: studioBridge.setRole(modelData.key, text)
                        }
                    }
                }
            }
        }
    }
}
