import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "components"
import "pages"
import "theme"

ApplicationWindow {
    id: root
    width: 1180
    height: 760
    minimumWidth: 920
    minimumHeight: 600
    visible: true
    title: "Theme Studio — " + studioBridge.themeName + (studioBridge.dirty ? " *" : "")
    color: Theme.bg
    property int currentPage: 0
    function syncTheme() { Theme.applyEngine(themeBridge.name, themeBridge.colorsJson, themeBridge.dark, themeBridge.fontFamily) }
    Component.onCompleted: syncTheme()
    onClosing: function(close) { studioBridge.closeSession() }
    Connections { target: themeBridge; function onThemeChanged() { root.syncTheme() } }
    ColumnLayout {
        anchors.fill: parent
        spacing: 0
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 62
            color: Theme.bgElevated
            border.color: Theme.border
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 18
                anchors.rightMargin: 18
                spacing: 10
                ColumnLayout { spacing: 0; Text { text: "Theme Studio"; color: Theme.textPrimary; font.family: Theme.fontFamily; font.pixelSize: 17; font.weight: Font.Bold }; Text { text: studioBridge.themeName + (studioBridge.dirty ? " · unsaved changes" : ""); color: studioBridge.dirty ? Theme.warn : Theme.textMuted; font.family: Theme.fontFamily; font.pixelSize: 11 } }
                Item { Layout.fillWidth: true }
                SecondaryButton { text: "Undo"; enabled: studioBridge.canUndo; onClicked: studioBridge.undo() }
                SecondaryButton { text: "Redo"; enabled: studioBridge.canRedo; onClicked: studioBridge.redo() }
                SecondaryButton { text: "Cancel"; enabled: studioBridge.dirty; onClicked: studioBridge.cancelChanges() }
                PrimaryButton { text: "Save & Apply"; enabled: studioBridge.themeName.length > 0; onClicked: studioBridge.saveAndApply() }
            }
        }
        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 0
            Rectangle {
                Layout.preferredWidth: 230
                Layout.fillHeight: true
                color: Theme.bgElevated
                border.color: Theme.border
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 16
                    spacing: 8
                    SidebarButton { text: "Themes"; selected: root.currentPage === 0; Layout.fillWidth: true; onClicked: root.currentPage = 0 }
                    SidebarButton { text: "Palette"; selected: root.currentPage === 1; Layout.fillWidth: true; onClicked: root.currentPage = 1 }
                    SidebarButton { text: "Style"; selected: root.currentPage === 2; Layout.fillWidth: true; onClicked: root.currentPage = 2 }
                    SidebarButton { text: "Inspector"; selected: root.currentPage === 3; Layout.fillWidth: true; onClicked: root.currentPage = 3 }
                    Item { Layout.fillHeight: true }
                    Rectangle {
                        Layout.fillWidth: true
                        implicitHeight: previewColumn.implicitHeight + 20
                        radius: Theme.radiusMedium
                        color: Theme.surface
                        border.color: Theme.border
                        ColumnLayout {
                            id: previewColumn
                            anchors.fill: parent
                            anchors.margins: 10
                            spacing: 6
                            RowLayout { Layout.fillWidth: true; Text { text: "Live preview"; color: Theme.textPrimary; font.family: Theme.fontFamily; font.pixelSize: 12; Layout.fillWidth: true }; Switch { checked: studioBridge.livePreview; onToggled: studioBridge.setLivePreview(checked) } }
                            SecondaryButton { text: "Preview now"; Layout.fillWidth: true; onClicked: studioBridge.previewNow() }
                            SecondaryButton { text: "Apply saved"; Layout.fillWidth: true; enabled: !studioBridge.dirty; onClicked: studioBridge.applySaved() }
                        }
                    }
                }
            }
            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                color: Theme.bg
                StackLayout { anchors.fill: parent; anchors.margins: 28; currentIndex: root.currentPage; ThemesPage {}; PalettePage {}; StylePage {}; InspectorPage {} }
            }
        }
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 34
            color: Theme.surface
            border.color: Theme.border
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 14
                anchors.rightMargin: 14
                Text { text: studioBridge.statusMessage; color: Theme.textSecondary; font.family: Theme.fontFamily; font.pixelSize: 11; elide: Text.ElideRight; Layout.fillWidth: true }
                Text { text: studioBridge.validationSummary; color: Theme.textMuted; font.family: Theme.fontFamily; font.pixelSize: 11 }
                Text { text: themeBridge.connected ? "theme contract connected" : "fallback UI palette"; color: themeBridge.connected ? Theme.success : Theme.warn; font.family: Theme.fontFamily; font.pixelSize: 11 }
            }
        }
    }
}
