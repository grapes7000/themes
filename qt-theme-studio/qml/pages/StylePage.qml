import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts
import "../components"
import "../theme"

Item {
    id: root
    property string colorKey: ""
    property var rows: JSON.parse(studioBridge.styleRowsJson)
    property bool sliderDragging: false
    property bool refreshPending: false
    function refreshRows() {
        if (sliderDragging) { refreshPending = true; return }
        rows = JSON.parse(studioBridge.styleRowsJson)
        refreshPending = false
    }
    Connections { target: studioBridge; function onStateChanged() { root.refreshRows() } }
    ColorDialog {
        id: colorPicker
        title: "Choose shadow color"
        onAccepted: studioBridge.setStyle(root.colorKey, selectedColor.toString())
    }
    ScrollView {
        anchors.fill: parent
        clip: true
        contentWidth: availableWidth
        ColumnLayout {
            width: parent.width
            spacing: 14
            Text { text: "Style"; color: Theme.textPrimary; font.family: Theme.fontFamily; font.pixelSize: 28; font.weight: Font.Bold }
            Text { text: "Adjust desktop effects using sliders and switches."; color: Theme.textSecondary; font.family: Theme.fontFamily; font.pixelSize: 13; wrapMode: Text.WordWrap; Layout.fillWidth: true }
            SectionCard {
                Layout.fillWidth: true
                title: "Desktop styling"
                Repeater {
                    model: root.rows
                    delegate: RowLayout {
                        required property var modelData
                        Layout.fillWidth: true
                        spacing: 12
                        Text { text: modelData.label; color: Theme.textSecondary; font.family: Theme.fontFamily; font.pixelSize: 13; Layout.preferredWidth: 200 }
                        Rectangle { visible: modelData.type === "color"; width: visible ? 28 : 0; height: 28; radius: 6; color: modelData.type === "color" && modelData.value ? modelData.value : "transparent"; border.color: Theme.borderStrong }
                        Switch {
                            visible: modelData.type === "boolstr"
                            checked: modelData.value.toLowerCase() === "true"
                            onClicked: studioBridge.setStyle(modelData.key, checked ? "true" : "false")
                        }
                        SecondaryButton {
                            visible: modelData.type === "color"
                            text: "Choose color"
                            onClicked: { root.colorKey = modelData.key; colorPicker.selectedColor = modelData.value; colorPicker.open() }
                        }
                        Slider {
                            id: styleSlider
                            objectName: "style." + modelData.key
                            visible: modelData.type === "int" || modelData.type === "float"
                            Layout.fillWidth: true
                            from: modelData.minimum
                            to: modelData.maximum
                            stepSize: modelData.step
                            snapMode: Slider.SnapAlways
                            value: Number(modelData.value)
                            Accessible.name: modelData.label
                            onMoved: if (!pressed) studioBridge.setStyle(modelData.key, String(value))
                            onPressedChanged: {
                                if (pressed) root.sliderDragging = true
                                else if (root.sliderDragging) {
                                    studioBridge.setStyle(modelData.key, String(value))
                                    root.sliderDragging = false
                                    if (root.refreshPending) root.refreshRows()
                                }
                            }
                        }
                        Text { visible: modelData.type === "int" || modelData.type === "float"; text: styleSlider.pressed ? Number(styleSlider.value.toFixed(3)) : modelData.value; color: Theme.textPrimary; Layout.preferredWidth: 60; horizontalAlignment: Text.AlignHCenter }
                    }
                }
            }
        }
    }
}
