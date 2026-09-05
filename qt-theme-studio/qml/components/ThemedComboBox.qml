import QtQuick
import QtQuick.Controls
import "../theme"

ComboBox {
    id: control
    implicitHeight: 38
    leftPadding: 12
    rightPadding: 12
    font.family: Theme.fontFamily
    font.pixelSize: 13

    contentItem: Text {
        leftPadding: control.leftPadding
        rightPadding: control.indicator.width + control.spacing
        text: control.displayText
        color: control.enabled ? Theme.textPrimary : Theme.textMuted
        font: control.font
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }
    background: Rectangle {
        radius: Theme.radiusSmall
        color: control.pressed ? Theme.surfaceActive : (control.hovered ? Theme.surfaceHover : Theme.bgElevated)
        border.color: control.activeFocus ? Theme.focusRing : Theme.border
    }
    indicator: Text {
        x: control.width - width - 12
        y: (control.height - height) / 2
        text: "⌄"
        color: Theme.textSecondary
        font.family: Theme.fontFamily
        font.pixelSize: 16
    }
    delegate: ItemDelegate {
        id: optionDelegate
        required property var modelData
        required property int index
        width: control.width
        height: 34
        highlighted: control.highlightedIndex === index
        contentItem: Text {
            text: modelData
            color: Theme.textPrimary
            font: control.font
            verticalAlignment: Text.AlignVCenter
            leftPadding: 12
            rightPadding: 12
            elide: Text.ElideRight
        }
        background: Rectangle {
            color: optionDelegate.highlighted ? Theme.accentSoft : Theme.surface
        }
    }
    popup: Popup {
        id: optionPopup
        y: control.height - 1
        width: control.width
        implicitHeight: Math.min(optionList.contentHeight + 2, 240)
        padding: 1
        contentItem: ListView {
            id: optionList
            clip: true
            implicitHeight: contentHeight
            model: control.popup.visible ? control.delegateModel : null
            currentIndex: control.highlightedIndex
        }
        background: Rectangle {
            color: Theme.surface
            border.color: Theme.border
            radius: Theme.radiusSmall
        }
    }
}
