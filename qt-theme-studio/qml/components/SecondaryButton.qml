import QtQuick
import QtQuick.Controls
import "../theme"

Button {
    id: control
    implicitHeight: 38
    leftPadding: 13
    rightPadding: 13
    font.family: Theme.fontFamily
    font.pixelSize: 13
    contentItem: Text { text: control.text; color: control.enabled ? Theme.textPrimary : Theme.textMuted; font: control.font; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
    background: Rectangle { radius: Theme.radiusMedium; color: control.hovered ? Theme.surfaceHover : Theme.surface; border.color: Theme.border }
}
