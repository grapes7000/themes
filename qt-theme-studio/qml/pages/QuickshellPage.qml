import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../components"
import "../theme"

Item {
    id: root
    property var rows: JSON.parse(studioBridge.quickshellRowsJson)
    property var roles: JSON.parse(studioBridge.roleNamesJson)
    Connections { target: studioBridge; function onStateChanged() { root.rows = JSON.parse(studioBridge.quickshellRowsJson) } }

    ScrollView {
        anchors.fill: parent
        clip: true
        contentWidth: availableWidth
        ColumnLayout {
            width: parent.width
            spacing: Theme.spacingMedium
            Text { text: "Quickshell"; color: Theme.textPrimary; font.family: Theme.fontFamily; font.pixelSize: 28; font.weight: Font.Bold }
            Text { text: "Controls for your Arch-WM Quickshell bar, drawers, and homepage. They are saved inside this theme and published through the watched theme contract—your hand-authored Quickshell QML and widget layout are never overwritten."; color: Theme.textSecondary; font.family: Theme.fontFamily; font.pixelSize: 13; wrapMode: Text.WordWrap; Layout.fillWidth: true }
            SectionCard {
                Layout.fillWidth: true
                title: "Live shell appearance"
                subtitle: "Quickshell watches theme changes, so committed edits update its surfaces without restarting the shell."
                Repeater {
                    model: root.rows
                    delegate: RowLayout {
                        required property var modelData
                        Layout.fillWidth: true
                        spacing: Theme.spacingSmall
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
                        TextField {
                            visible: modelData.kind !== "choice" && modelData.kind !== "role"
                            text: modelData.value
                            selectByMouse: true
                            Layout.fillWidth: true
                            color: Theme.textPrimary
                            background: Rectangle { color: Theme.bgElevated; border.color: parent.activeFocus ? Theme.focusRing : Theme.border; radius: Theme.radiusSmall }
                            onEditingFinished: studioBridge.setQuickshellValue(modelData.path, text)
                        }
                    }
                }
            }
        }
    }
}
