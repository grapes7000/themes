import QtQuick
import QtQuick.Controls
import "../theme"

Button {
    id: control
    property bool selected: false
    implicitHeight: 42
    font.family: Theme.fontFamily
    font.pixelSize: 14
    contentItem: Text { text: control.text; color: control.selected ? Theme.onAccent : Theme.textSecondary; font: control.font; verticalAlignment: Text.AlignVCenter; leftPadding: 12 }
    background: Rectangle { radius: Theme.radiusMedium; color: control.selected ? Theme.accent : (control.hovered ? Theme.surfaceHover : "transparent") }
}
