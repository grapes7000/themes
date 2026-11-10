import QtQuick
import QtQuick.Layouts
import "../theme"

// An illustrative bar and drawer, using the same theme values as Quickshell.
Rectangle {
    id: root
    objectName: "shell-example"
    property color backgroundColor: "#181825"
    property color barColor: "#242433"
    property color drawerColor: "#303040"
    property color buttonColor: "#303040"
    property color outlineColor: "#606070"
    property color drawerOutlineColor: "#606070"
    property color accentColor: "#89b4fa"
    property color textColor: "#ffffff"
    property color hoverColor: "#454557"
    property real barOpacity: 1
    property real drawerOpacity: 1
    property real outlineOpacity: 1
    property real drawerOutlineOpacity: 1
    property int barRadius: 4
    property int buttonRadius: 3
    property int drawerRadius: 8
    property int drawerWidth: 420
    property int outlineWidth: 1
    property bool quietButtons: true
    property string barRole: "surface_0"
    property string drawerRole: "surface_1"
    property string barOutlineRole: "border_subtle"
    property string drawerOutlineRole: "border_subtle"
    signal inspected(string part, var roles)
    function withAlpha(c, a) { return Qt.rgba(c.r, c.g, c.b, a) }

    implicitHeight: 225
    color: backgroundColor
    radius: 8
    clip: true
    MouseArea { anchors.fill: parent; acceptedButtons: Qt.RightButton; onClicked: root.inspected("Example background", ["bg"]) }

    Rectangle {
        id: bar
        anchors { top: parent.top; left: parent.left; right: parent.right; margins: 12 }
        height: 42
        radius: root.barRadius
        color: root.withAlpha(root.barColor, root.barOpacity)
        border.width: root.outlineWidth
        border.color: root.withAlpha(root.outlineColor, root.outlineOpacity)
        MouseArea { anchors.fill: parent; acceptedButtons: Qt.RightButton; onClicked: root.inspected("Bar surface and outline", [root.barRole, root.barOutlineRole]) }
        Row {
            anchors { left: parent.left; verticalCenter: parent.verticalCenter; leftMargin: 8 }
            spacing: 8
            Repeater {
                model: ["Menu", "Hover me", "12:30"]
                Rectangle {
                    required property string modelData
                    width: buttonText.implicitWidth + 20
                    height: 28
                    radius: root.buttonRadius
                    color: pointer.containsMouse ? root.withAlpha(root.hoverColor, root.quietButtons ? 0.42 : 0.94) : root.withAlpha(root.buttonColor, root.quietButtons ? 0 : 0.72)
                    border.width: root.outlineWidth
                    border.color: pointer.containsMouse ? root.withAlpha(root.accentColor, root.quietButtons ? 0.34 : 0.62) : root.withAlpha(root.outlineColor, root.quietButtons ? 0 : Math.max(0.24, root.outlineOpacity * 0.72))
                    Text { id: buttonText; anchors.centerIn: parent; text: modelData; color: root.textColor; font.pixelSize: 12 }
                    MouseArea {
                        id: pointer; anchors.fill: parent; hoverEnabled: true; acceptedButtons: Qt.RightButton
                        onClicked: root.inspected("Hovered bar button: background, outline and text (opacity may blend colors)", ["hover", "accent", "text"])
                    }
                }
            }
        }
    }
    Rectangle {
        objectName: "shell-preview-drawer"
        anchors { top: bar.bottom; left: parent.left; margins: 12 }
        width: Math.min(root.drawerWidth / 2, parent.width - 24)
        height: 118
        radius: root.drawerRadius
        color: root.withAlpha(root.drawerColor, root.drawerOpacity)
        border.width: root.outlineWidth
        border.color: root.withAlpha(root.drawerOutlineColor, root.drawerOutlineOpacity)
        MouseArea { anchors.fill: parent; acceptedButtons: Qt.RightButton; onClicked: root.inspected("Drawer surface and outline", [root.drawerRole, root.drawerOutlineRole]) }
        Column {
            anchors { fill: parent; margins: 14 }
            spacing: 10
            Text { text: "Example drawer"; color: root.textColor; font.pixelSize: 14; font.bold: true }
            Text { text: "Buttons, corners and colors"; color: root.textColor; opacity: 0.75; font.pixelSize: 12 }
            Rectangle { width: 100; height: 5; radius: 2; color: root.accentColor }
        }
    }
}
