import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../components"
import "../theme"

Item {
    ColumnLayout {
        anchors.fill: parent
        spacing: 14
        RowLayout {
            Layout.fillWidth: true
            Text { text: "Themes"; color: Theme.textPrimary; font.family: Theme.fontFamily; font.pixelSize: 28; font.weight: Font.Bold }
            Item { Layout.fillWidth: true }
            SecondaryButton { text: "Refresh"; onClicked: studioBridge.reloadThemes() }
        }
        Text { text: "Pick a saved theme. With live preview on, selecting one previews it immediately without saving anything."; color: Theme.textSecondary; font.family: Theme.fontFamily; font.pixelSize: 13; wrapMode: Text.WordWrap; Layout.fillWidth: true }
        ListView {
            id: themeList
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 8
            clip: true
            model: JSON.parse(studioBridge.themesJson)
            delegate: Rectangle {
                required property string modelData
                width: themeList.width
                height: 54
                radius: Theme.radiusMedium
                color: modelData === studioBridge.themeName ? Theme.accentSoft : Theme.surface
                border.color: modelData === studioBridge.themeName ? Theme.accent : Theme.border
                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 14
                    anchors.rightMargin: 10
                    Text { text: modelData; color: Theme.textPrimary; font.family: Theme.fontFamily; font.pixelSize: 14; font.weight: modelData === studioBridge.themeName ? Font.DemiBold : Font.Normal; Layout.fillWidth: true }
                    Text { visible: modelData === studioBridge.activeTheme; text: "ACTIVE"; color: Theme.success; font.family: Theme.fontFamily; font.pixelSize: 10; font.weight: Font.Bold }
                    SecondaryButton { text: modelData === studioBridge.themeName ? "Selected" : "Edit"; enabled: modelData !== studioBridge.themeName; onClicked: studioBridge.selectTheme(modelData) }
                }
            }
        }
    }
}
