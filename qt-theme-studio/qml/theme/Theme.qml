pragma Singleton
import QtQuick

QtObject {
    property bool dark: true
    property string engineName: "Built-in"
    property string fontFamily: ""
    property var _engine: ({})
    property int _version: 0
    function applyEngine(name, colorsJson, isDark, font) { engineName = name || "Built-in"; fontFamily = font || ""; dark = isDark; try { _engine = colorsJson ? JSON.parse(colorsJson) : ({}) } catch (e) { _engine = ({}) }; _version++ }
    function fallback(name) {
        const darkPalette = {bg:"#141319",bgElevated:"#1B1A22",surface:"#211F2A",surfaceAlt:"#262432",surfaceHover:"#2C2A3A",surfaceActive:"#322F44",border:"#33303F",borderStrong:"#46415C",textPrimary:"#ECE9F4",textSecondary:"#A8A3BA",textMuted:"#6F6A80",accent:"#8B7CF8",accentStrong:"#A294FB",accentSoft:"#2A2740",accentSoftHover:"#33305A",success:"#5FD38C",warn:"#E9C46A",danger:"#F2768A",info:"#7CB8F8",focusRing:"#A294FB",onAccent:"#14131A",selection:"#8B7CF8"}
        const lightPalette = {bg:"#F6F5FB",bgElevated:"#FFFFFF",surface:"#FFFFFF",surfaceAlt:"#F1EFF7",surfaceHover:"#E9E6F2",surfaceActive:"#E0DCF0",border:"#E2DFEE",borderStrong:"#C8C2DE",textPrimary:"#211F2A",textSecondary:"#5C576E",textMuted:"#8F8AA0",accent:"#6C5CE7",accentStrong:"#5748C9",accentSoft:"#EEEBFB",accentSoftHover:"#E3DEF7",success:"#2F9E5F",warn:"#B8860B",danger:"#D64563",info:"#2D7DD2",focusRing:"#6C5CE7",onAccent:"#FFFFFF",selection:"#6C5CE7"}
        return (dark ? darkPalette : lightPalette)[name]
    }
    function c(name) { const version = _version; return (version >= 0 && _engine[name]) ? _engine[name] : fallback(name) }
    readonly property color bg: c("bg")
    readonly property color bgElevated: c("bgElevated")
    readonly property color surface: c("surface")
    readonly property color surfaceAlt: c("surfaceAlt")
    readonly property color surfaceHover: c("surfaceHover")
    readonly property color surfaceActive: c("surfaceActive")
    readonly property color border: c("border")
    readonly property color borderStrong: c("borderStrong")
    readonly property color textPrimary: c("textPrimary")
    readonly property color textSecondary: c("textSecondary")
    readonly property color textMuted: c("textMuted")
    readonly property color accent: c("accent")
    readonly property color accentStrong: c("accentStrong")
    readonly property color accentSoft: c("accentSoft")
    readonly property color accentSoftHover: c("accentSoftHover")
    readonly property color success: c("success")
    readonly property color warn: c("warn")
    readonly property color danger: c("danger")
    readonly property color info: c("info")
    readonly property color focusRing: c("focusRing")
    readonly property color onAccent: c("onAccent")
    readonly property color selection: c("selection")
    readonly property int radiusSmall: 6
    readonly property int radiusMedium: 10
    readonly property int radiusLarge: 14
    readonly property int spacingSmall: 8
    readonly property int spacingMedium: 12
    readonly property int spacingLarge: 16
    readonly property int spacingXLarge: 24
}
