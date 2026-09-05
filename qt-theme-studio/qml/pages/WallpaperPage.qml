import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../components"
import "../theme"

Item {
    id: root
    property var wallpaperModel: JSON.parse(studioBridge.wallpapersJson)
    property var themeModel: JSON.parse(studioBridge.themesJson)
    property var recolorRegions: JSON.parse(studioBridge.recolorRegionsJson)
    property var semanticRoles: JSON.parse(studioBridge.semanticRolesJson)

    Connections {
        target: studioBridge
        function onWallpapersChanged() { root.wallpaperModel = JSON.parse(studioBridge.wallpapersJson) }
        function onThemesChanged() { root.themeModel = JSON.parse(studioBridge.themesJson) }
        function onRecolorChanged() { root.recolorRegions = JSON.parse(studioBridge.recolorRegionsJson) }
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: Theme.spacingMedium

        RowLayout {
            Layout.fillWidth: true
            Text { text: "Wallpapers"; color: Theme.textPrimary; font.family: Theme.fontFamily; font.pixelSize: 28; font.weight: Font.Bold }
            Item { Layout.fillWidth: true }
            SecondaryButton { text: "Refresh"; onClicked: studioBridge.refreshWallpapers() }
        }

        Text {
            text: "Apply changes the desktop now. Bind saves this image as the wallpaper restored whenever the selected theme is applied."
            color: Theme.textSecondary
            font.family: Theme.fontFamily
            font.pixelSize: 13
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
        }

        RowLayout {
            Layout.fillWidth: true
            Text { text: "Folder"; color: Theme.textSecondary; font.family: Theme.fontFamily; font.pixelSize: 12 }
            TextField {
                id: folderField
                text: studioBridge.wallpaperDirectory
                Layout.fillWidth: true
                selectByMouse: true
                color: Theme.textPrimary
                font.family: Theme.fontFamily
                background: Rectangle { color: Theme.bgElevated; border.color: folderField.activeFocus ? Theme.focusRing : Theme.border; radius: Theme.radiusSmall }
                onEditingFinished: studioBridge.setWallpaperDirectory(text)
            }
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: Theme.spacingLarge

            Rectangle {
                Layout.preferredWidth: Math.max(360, parent.width * 0.55)
                Layout.fillHeight: true
                color: Theme.surface
                border.color: Theme.border
                radius: Theme.radiusMedium

                Image {
                    anchors.fill: parent
                    anchors.margins: 1
                    source: studioBridge.recolorPreviewUrl || studioBridge.selectedWallpaperUrl
                    fillMode: Image.PreserveAspectFit
                    asynchronous: true
                    cache: false
                }
                Text {
                    anchors.centerIn: parent
                    visible: studioBridge.selectedWallpaperUrl === ""
                    text: "No wallpapers found\nAdd images to the folder above."
                    horizontalAlignment: Text.AlignHCenter
                    color: Theme.textMuted
                    font.family: Theme.fontFamily
                }
            }

            ColumnLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: Theme.spacingSmall

                Text { text: studioBridge.selectedWallpaperName || "Select a wallpaper"; color: Theme.textPrimary; font.family: Theme.fontFamily; font.pixelSize: 15; font.weight: Font.DemiBold; elide: Text.ElideRight; Layout.fillWidth: true }
                PrimaryButton { text: "Apply now"; enabled: studioBridge.selectedWallpaperUrl !== ""; Layout.fillWidth: true; onClicked: studioBridge.applySelectedWallpaper() }

                Text { text: "Bind selected image to"; color: Theme.textSecondary; font.family: Theme.fontFamily; font.pixelSize: 12 }
                ComboBox {
                    id: themePicker
                    model: root.themeModel
                    Layout.fillWidth: true
                    currentIndex: Math.max(0, root.themeModel.indexOf(studioBridge.themeName))
                }
                SecondaryButton { text: "Bind to theme"; enabled: studioBridge.selectedWallpaperUrl !== "" && themePicker.currentText !== ""; Layout.fillWidth: true; onClicked: studioBridge.bindSelectedWallpaper(themePicker.currentText) }

                Rectangle { Layout.fillWidth: true; implicitHeight: 1; color: Theme.border }
                Text { text: "Semantic recolor"; color: Theme.textSecondary; font.family: Theme.fontFamily; font.pixelSize: 12 }
                SecondaryButton { text: studioBridge.recolorTemplateName ? "Re-import selected image" : "Import selected image"; enabled: studioBridge.selectedWallpaperUrl !== ""; Layout.fillWidth: true; onClicked: studioBridge.importSelectedForRecolor() }
                ListView {
                    id: regionsList
                    visible: root.recolorRegions.length > 0
                    Layout.fillWidth: true
                    Layout.preferredHeight: visible ? Math.min(150, contentHeight) : 0
                    clip: true
                    spacing: 4
                    model: root.recolorRegions
                    delegate: RowLayout {
                        id: regionRow
                        required property var modelData
                        required property int index
                        width: regionsList.width
                        Text { text: modelData.source; color: Theme.textPrimary; font.family: Theme.fontFamily; font.pixelSize: 11; Layout.preferredWidth: 78 }
                        ComboBox {
                            id: rolePicker
                            model: root.semanticRoles
                            currentIndex: Math.max(0, root.semanticRoles.indexOf(modelData.role))
                            Layout.fillWidth: true
                            onActivated: studioBridge.setRecolorRole(regionRow.index, currentText)
                        }
                    }
                }
                SecondaryButton { text: "Preview recolor"; enabled: studioBridge.recolorTemplateName !== "" && themePicker.currentText !== ""; Layout.fillWidth: true; onClicked: studioBridge.previewRecolor(themePicker.currentText) }
                PrimaryButton { text: "Bind recolored to theme"; enabled: studioBridge.recolorTemplateName !== "" && themePicker.currentText !== ""; Layout.fillWidth: true; onClicked: studioBridge.bindRecolorToTheme(themePicker.currentText) }

                Rectangle { Layout.fillWidth: true; implicitHeight: 1; color: Theme.border }
                Text { text: "Library"; color: Theme.textSecondary; font.family: Theme.fontFamily; font.pixelSize: 12 }
                ListView {
                    id: wallpaperList
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    spacing: 6
                    model: root.wallpaperModel
                    delegate: Rectangle {
                        required property var modelData
                        width: wallpaperList.width
                        height: 46
                        radius: Theme.radiusSmall
                        color: index === studioBridge.selectedWallpaperIndex ? Theme.accentSoft : Theme.bgElevated
                        border.color: index === studioBridge.selectedWallpaperIndex ? Theme.accent : Theme.border
                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 8
                            anchors.rightMargin: 8
                            Image { source: modelData.url; Layout.preferredWidth: 48; Layout.preferredHeight: 32; fillMode: Image.PreserveAspectCrop; asynchronous: true }
                            Text { text: modelData.name; color: Theme.textPrimary; font.family: Theme.fontFamily; font.pixelSize: 12; elide: Text.ElideRight; Layout.fillWidth: true }
                        }
                        MouseArea { anchors.fill: parent; onClicked: studioBridge.selectWallpaper(index) }
                    }
                }
            }
        }
    }
}
