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
            Text { text: "Inspector"; color: Theme.textPrimary; font.family: Theme.fontFamily; font.pixelSize: 28; font.weight: Font.Bold }
            SectionCard {
                Layout.fillWidth: true
                title: "Validation"
                subtitle: studioBridge.validationSummary
                Repeater {
                    model: JSON.parse(studioBridge.validationJson)
                    delegate: Text {
                        required property var modelData
                        Layout.fillWidth: true
                        text: (modelData.level === "error" ? "✕ " : "• ") + modelData.path + ": " + modelData.message
                        color: modelData.level === "error" ? Theme.danger : Theme.warn
                        font.family: Theme.fontFamily
                        font.pixelSize: 12
                        wrapMode: Text.WordWrap
                    }
                }
                Text { visible: JSON.parse(studioBridge.validationJson).length === 0; text: "No validation issues."; color: Theme.success; font.family: Theme.fontFamily; font.pixelSize: 13 }
            }
            SectionCard {
                Layout.fillWidth: true
                title: "Coming next"
                subtitle: "The existing TUI still owns the deeper component editors, Waybar layout tools, wallpaper studio, comparisons, search, and theme management while they are migrated page by page."
                Text { text: "This page is intentionally a stand-in instead of pretending feature parity already exists."; color: Theme.textSecondary; font.family: Theme.fontFamily; font.pixelSize: 13; wrapMode: Text.WordWrap; Layout.fillWidth: true }
            }
        }
    }
}
