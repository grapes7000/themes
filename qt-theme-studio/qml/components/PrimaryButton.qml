import QtQuick
import QtQuick.Controls
import "../theme"

Button {
    id: control
    implicitHeight: 38
    leftPadding: 14
    rightPadding: 14
    font.family: Theme.fontFamily
    font.pixelSize: 13
    font.weight: Font.DemiBold
    contentItem: Text { text: control.text; color: control.enabled ? Theme.onAccent : Theme.textMuted; font: control.font; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
    background: Rectangle { radius: Theme.radiusMedium; color: control.enabled ? (control.hovered ? Theme.accentStrong : Theme.accent) : Theme.surfaceAlt; border.color: control.enabled ? Theme.accentStrong : Theme.border }
}
