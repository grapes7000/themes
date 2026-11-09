import QtQuick
import QtQuick.Layouts
import "../theme"

ColumnLayout {
    id: root
    property var paletteRows: []
    property var terminalSettings: ({})
    property string inspectedPart: ""
    property var inspectedRoles: []
    readonly property string inspection: inspectedPart ? inspectionText() : "Right-click an example to see its color roles."
    function row(key) { return paletteRows.find(item => item.key === key) }
    function resolved(key, fallback) {
        const item = row(key)
        return item && item.value ? key : fallback
    }
    function color(key, fallback) {
        if (/^#[0-9a-fA-F]{6}$/.test(key)) return key
        const item = row(resolved(key, fallback || "text"))
        return item && item.value ? item.value : "#808080"
    }
    function inspectionText() {
        const descriptions = inspectedRoles.map(function(key) {
            const item = row(key)
            return item ? item.label + " (" + key + "): " + (item.value || "not set") : key
        })
        return inspectedPart + " — " + descriptions.join("; ")
    }
    function describe(part, keys) {
        inspectedPart = part
        inspectedRoles = keys
    }
    component Inspect: MouseArea {
        property string part: ""
        property var roles: []
        anchors.fill: parent
        acceptedButtons: Qt.RightButton
        onClicked: root.describe(part, roles)
    }
    spacing: 5
    RowLayout {
        Layout.fillWidth: true
        spacing: 10
        Rectangle {
            id: terminal
            objectName: "palette-terminal-background"
            Layout.fillWidth: true
            Layout.preferredHeight: 160
            radius: 8; color: root.color("bg"); border.color: root.color("accent")
            Inspect { part: "Terminal background and active border"; roles: ["bg", "accent"] }
            ColumnLayout {
                anchors.fill: parent; anchors.margins: 10; spacing: 3
                RowLayout {
                    Rectangle {
                        implicitWidth: 82; implicitHeight: 20; radius: 4
                        color: root.color(root.terminalSettings.active_tab_role || "accent")
                        Text { anchors.centerIn: parent; text: "Terminal"; color: root.color("on_accent"); font.pixelSize: 11 }
                        Inspect { part: "Active terminal tab"; roles: [root.terminalSettings.active_tab_role || "accent", "on_accent"] }
                    }
                    Text { text: "Example · Kitty"; color: root.color("text_dim"); font.pixelSize: 10 }
                }
                RowLayout {
                    Text { objectName: "palette-prompt-directory"; text: "~/projects"; color: root.color("accent"); font.family: "monospace"; font.pixelSize: 12; Inspect { part: "Starship directory (minimal example)"; roles: ["accent"] } }
                    Text { text: "git:main"; color: root.color("accent2"); font.family: "monospace"; font.pixelSize: 12; Inspect { part: "Starship branch (minimal example)"; roles: ["accent2"] } }
                }
                RowLayout {
                    Text { text: "❯"; color: root.color("ansi_green", "success"); font.family: "monospace"; font.pixelSize: 12; Inspect { part: "Starship success prompt (minimal example)"; roles: [root.resolved("ansi_green", "success")] } }
                    Text { text: "fastfetch"; color: root.color("text"); font.family: "monospace"; font.pixelSize: 12; Inspect { part: "Terminal command text"; roles: ["text"] } }
                }
                RowLayout {
                    Text { objectName: "palette-fastfetch-logo"; text: "◈"; color: root.color("ansi_cyan", "text"); font.pixelSize: 25; Inspect { part: "Example Fastfetch logo (terminal cyan)"; roles: [root.resolved("ansi_cyan", "text")] } }
                    ColumnLayout {
                        spacing: 0
                        Text { text: "Arch Linux"; color: root.color("ansi_blue", "text"); font.family: "monospace"; font.pixelSize: 11; Inspect { part: "Example Fastfetch label (terminal blue)"; roles: [root.resolved("ansi_blue", "text")] } }
                        Text { text: "Shell: zsh"; color: root.color("text"); font.family: "monospace"; font.pixelSize: 11; Inspect { part: "Example Fastfetch text"; roles: ["text"] } }
                    }
                }
                Item { Layout.fillHeight: true }
            }
        }
        Rectangle {
            objectName: "palette-app-background"
            Layout.fillWidth: true
            Layout.preferredHeight: 160
            radius: 8; color: root.color("bg"); border.color: root.color("border_normal")
            Inspect { part: "App background and border"; roles: ["bg", "border_normal"] }
            ColumnLayout {
                anchors.fill: parent; anchors.margins: 10; spacing: 5
                Text { text: "Example Qt app"; color: root.color("text"); font.pixelSize: 12; font.bold: true; Inspect { part: "App title"; roles: ["text"] } }
                RowLayout {
                    Rectangle { implicitWidth: 75; implicitHeight: 22; radius: 4; color: root.color("surface_0"); Text { anchors.centerIn: parent; text: "Workspace"; color: root.color("text"); font.pixelSize: 10 } Inspect { part: "Selected app tab"; roles: ["surface_0", "text"] } }
                    Rectangle { implicitWidth: 55; implicitHeight: 22; radius: 4; color: root.color("surface_1"); Text { anchors.centerIn: parent; text: "Notes"; color: root.color("text_dim"); font.pixelSize: 10 } Inspect { part: "Inactive app tab"; roles: ["surface_1", "text_dim"] } }
                }
                Rectangle {
                    Layout.fillWidth: true; Layout.fillHeight: true; radius: 5
                    color: root.color("surface_0"); border.color: root.color("border_normal")
                    Inspect { part: "App panel and border"; roles: ["surface_0", "border_normal"] }
                    ColumnLayout {
                        anchors.fill: parent; anchors.margins: 7; spacing: 4
                        Text { text: "Your workspace"; color: root.color("text"); font.pixelSize: 11; Inspect { part: "App heading"; roles: ["text"] } }
                        Text { text: "A preview of common controls"; color: root.color("text_dim"); font.pixelSize: 10; Inspect { part: "App secondary text"; roles: ["text_dim"] } }
                        Rectangle { objectName: "palette-app-button"; implicitWidth: 80; implicitHeight: 23; radius: 4; color: root.color("accent"); Text { anchors.centerIn: parent; text: "Continue"; color: root.color("on_accent"); font.pixelSize: 10 } Inspect { part: "App accent button"; roles: ["accent", "on_accent"] } }
                        Item { Layout.fillHeight: true }
                    }
                }
            }
        }
    }
    Text {
        objectName: "palette-inspection"
        text: root.inspection; color: Theme.textPrimary; font.family: Theme.fontFamily
        font.pixelSize: 11; wrapMode: Text.WordWrap; Layout.fillWidth: true
    }
    Text { text: "Illustrations: Starship styles and Fastfetch configurations can look different."; color: Theme.textMuted; font.pixelSize: 10; Layout.fillWidth: true; elide: Text.ElideRight }
}
