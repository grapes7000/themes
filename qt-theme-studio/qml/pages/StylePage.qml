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
            Text { text: "Style"; color: Theme.textPrimary; font.family: Theme.fontFamily; font.pixelSize: 28; font.weight: Font.Bold }
            Text { text: "First-pass style controls from the existing theme schema. Numeric fields accept integers/decimals; blur and shadow accept true or false."; color: Theme.textSecondary; font.family: Theme.fontFamily; font.pixelSize: 13; wrapMode: Text.WordWrap; Layout.fillWidth: true }
            SectionCard {
                Layout.fillWidth: true
                title: "Desktop styling"
                Repeater {
                    model: JSON.parse(studioBridge.styleRowsJson)
                    delegate: RowLayout {
                        required property var modelData
                        Layout.fillWidth: true
                        spacing: 12
                        Text { text: modelData.label; color: Theme.textSecondary; font.family: Theme.fontFamily; font.pixelSize: 13; Layout.preferredWidth: 200 }
                        Rectangle { visible: modelData.type === "color"; width: visible ? 28 : 0; height: 28; radius: 6; color: modelData.type === "color" && modelData.value ? modelData.value : "transparent"; border.color: Theme.borderStrong }
                        TextField {
                            Layout.fillWidth: true
                            text: modelData.value
                            selectByMouse: true
                            font.family: Theme.fontFamily
                            color: Theme.textPrimary
                            background: Rectangle { color: Theme.bgElevated; border.color: parent.activeFocus ? Theme.focusRing : Theme.border; radius: Theme.radiusSmall }
                            onEditingFinished: studioBridge.setStyle(modelData.key, text)
                        }
                    }
                }
            }
        }
    }
}
