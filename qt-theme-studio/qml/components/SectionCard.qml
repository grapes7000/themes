import QtQuick
import QtQuick.Layouts
import "../theme"

Rectangle {
    id: card
    default property alias content: contentColumn.data
    property string title: ""
    property string subtitle: ""
    color: Theme.surface
    border.color: Theme.border
    radius: Theme.radiusLarge
    implicitHeight: contentColumn.implicitHeight + 32
    ColumnLayout {
        id: contentColumn
        anchors.fill: parent
        anchors.margins: 16
        spacing: 10
        Text { visible: card.title.length > 0; text: card.title; color: Theme.textPrimary; font.family: Theme.fontFamily; font.pixelSize: 16; font.weight: Font.DemiBold; Layout.fillWidth: true }
        Text { visible: card.subtitle.length > 0; text: card.subtitle; color: Theme.textMuted; font.family: Theme.fontFamily; font.pixelSize: 12; wrapMode: Text.WordWrap; Layout.fillWidth: true }
    }
}
