import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../components"
import "../theme"

Item {
    id: root
    property var rows: JSON.parse(studioBridge.windowRowsJson)
    property var presets: JSON.parse(studioBridge.windowPresetsJson)
    property var roles: JSON.parse(studioBridge.roleNamesJson)
    property bool advancedFields: false
    Connections { target: studioBridge; function onStateChanged() { root.rows = JSON.parse(studioBridge.windowRowsJson) } }

    ScrollView {
        anchors.fill: parent
        clip: true
        contentWidth: availableWidth
        ColumnLayout {
            width: parent.width
            spacing: Theme.spacingMedium
            Text { text: "Windows & Effects"; color: Theme.textPrimary; font.family: Theme.fontFamily; font.pixelSize: 28; font.weight: Font.Bold }
            Text { text: "These controls generate the Hyprland window decoration block. With Live preview enabled, each committed change reaches the desktop immediately; Cancel restores the starting theme."; color: Theme.textSecondary; font.family: Theme.fontFamily; font.pixelSize: 13; wrapMode: Text.WordWrap; Layout.fillWidth: true }
            SectionCard {
                Layout.fillWidth: true
                title: "Starting points"
                subtitle: "Presets are editable bundles, not locked styles."
                Flow {
                    Layout.fillWidth: true
                    spacing: Theme.spacingSmall
                    Repeater {
                        model: root.presets
                        delegate: SecondaryButton {
                            required property string modelData
                            text: modelData.replace(/_/g, " ")
                            onClicked: studioBridge.setWindowPreset(modelData)
                        }
                    }
                }
            }
            SectionCard {
                Layout.fillWidth: true
                title: "Fine tune"
                subtitle: root.advancedFields ? "All Windows fields. Left/Right adjusts a focused slider by one TUI step." : "Simple fields. Show advanced fields for the full TUI Windows room."
                RowLayout {
                    Layout.fillWidth: true
                    SecondaryButton {
                        text: root.advancedFields ? "Simple fields" : "Show advanced"
                        onClicked: root.advancedFields = !root.advancedFields
                    }
                    Item { Layout.fillWidth: true }
                    SecondaryButton { text: "Reset Windows"; onClicked: studioBridge.resetWindows() }
                }
                Repeater {
                    model: root.rows
                    delegate: RowLayout {
                        required property var modelData
                        Layout.fillWidth: true
                        visible: !modelData.advanced || root.advancedFields
                        spacing: Theme.spacingSmall
                        Text { text: modelData.label; color: Theme.textSecondary; font.family: Theme.fontFamily; font.pixelSize: 13; Layout.preferredWidth: 210; elide: Text.ElideRight }
                        ThemedComboBox {
                            visible: modelData.kind === "choice"
                            model: modelData.choices
                            currentIndex: Math.max(0, modelData.choices.indexOf(modelData.value))
                            Layout.fillWidth: true
                            onActivated: studioBridge.setWindowValue(modelData.path, currentText)
                        }
                        ThemedComboBox {
                            visible: modelData.kind === "role"
                            model: root.roles
                            currentIndex: Math.max(0, root.roles.indexOf(modelData.value))
                            Layout.fillWidth: true
                            onActivated: studioBridge.setWindowValue(modelData.path, currentText)
                        }
                        Switch {
                            visible: modelData.kind === "bool"
                            checked: modelData.value === "True" || modelData.value === "true"
                            onToggled: studioBridge.setWindowValue(modelData.path, checked ? "true" : "false")
                            Keys.onLeftPressed: function(event) {
                                studioBridge.adjustWindowValue(modelData.path, -1)
                                event.accepted = true
                            }
                            Keys.onRightPressed: function(event) {
                                studioBridge.adjustWindowValue(modelData.path, 1)
                                event.accepted = true
                            }
                        }
                        Slider {
                            id: numericSlider
                            visible: modelData.kind === "int" || modelData.kind === "float"
                            from: modelData.minimum === null ? 0 : modelData.minimum
                            to: modelData.maximum === null ? 100 : modelData.maximum
                            stepSize: modelData.step === null ? 1 : modelData.step
                            value: Number(modelData.value)
                            Layout.fillWidth: true
                            Accessible.name: modelData.label
                            Keys.onLeftPressed: function(event) {
                                studioBridge.adjustWindowValue(modelData.path, -1)
                                event.accepted = true
                            }
                            Keys.onRightPressed: function(event) {
                                studioBridge.adjustWindowValue(modelData.path, 1)
                                event.accepted = true
                            }
                            onMoved: studioBridge.setWindowValue(modelData.path, String(value))
                        }
                        TextField {
                            visible: modelData.kind !== "choice" && modelData.kind !== "role" && modelData.kind !== "bool"
                            text: modelData.value
                            selectByMouse: true
                            Layout.preferredWidth: 88
                            color: Theme.textPrimary
                            background: Rectangle { color: Theme.bgElevated; border.color: parent.activeFocus ? Theme.focusRing : Theme.border; radius: Theme.radiusSmall }
                            onEditingFinished: studioBridge.setWindowValue(modelData.path, text)
                        }
                        Text { visible: modelData.advanced; text: "advanced"; color: Theme.textMuted; font.pixelSize: 11 }
                    }
                }
            }
        }
    }
}
