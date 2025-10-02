#!/usr/bin/env bash
# DXVK install script (minimal, standalone)
# 用法：
#   ./setup_dxvk.sh install   [--with-wine /path/to/wine]
#   ./setup_dxvk.sh uninstall [--with-wine /path/to/wine]

set -e

# 默认 Wine
WINE=${WINE:-wine}
ACTION=${1:-help}
shift || true

# 解析可选参数
while [[ $# -gt 0 ]]; do
    case "$1" in
        --with-wine)
            WINE="$2"
            shift 2
            ;;
        *)
            echo "未知参数: $1"
            exit 1
            ;;
    esac
done

# Wine 前缀
WINEPREFIX=${WINEPREFIX:-$HOME/.wine}

# 需要处理的 DLL
DLLS32=(d3d8 d3d9 d3d10core d3d11 dxgi)
DLLS64=("${DLLS32[@]}")

# 系统目录
SYS32="$WINEPREFIX/drive_c/windows/system32"
SYSWOW64="$WINEPREFIX/drive_c/windows/syswow64"

# 颜色
red=$(tput setaf 1)
green=$(tput setaf 2)
reset=$(tput sgr0)

die() {
    echo "${red}$*${reset}" >&2
    exit 1
}

ensure_wineboot() {
    if [[ ! -d "$SYS32" ]]; then
        echo "Wine prefix 未初始化，正在 wineboot..."
        "$WINE" wineboot -u
    fi
}

install_dll() {
    local arch=$1 dll=$2 destdir=$3
    local src="x64"
    [[ "$arch" == "x32" ]] && src="x32"

    if [[ -f "$src/$dll.dll" ]]; then
        cp -v "$src/$dll.dll" "$destdir/$dll.dll"
        "$WINE" reg add "HKEY_CURRENT_USER\\Software\\Wine\\DllOverrides" /v "$dll" /d native /f >/dev/null
    else
        echo "${red}警告：$src/$dll.dll 不存在，跳过${reset}"
    fi
}

uninstall_dll() {
    local dll=$1 destdir=$2
    if [[ -f "$destdir/$dll.dll" ]]; then
        rm -v "$destdir/$dll.dll"
    fi
    "$WINE" reg delete "HKEY_CURRENT_USER\\Software\\Wine\\DllOverrides" /v "$dll" /f >/dev/null 2>&1 || true
}

case "$ACTION" in
    install)
        ensure_wineboot
        echo "安装 DXVK → $WINEPREFIX"
        for dll in "${DLLS64[@]}"; do
            install_dll x64 "$dll" "$SYS32"
        done
        for dll in "${DLLS32[@]}"; do
            install_dll x32 "$dll" "$SYSWOW64"
        done
        echo "${green}DXVK 安装完成${reset}"
        ;;
    uninstall)
        echo "卸载 DXVK ← $WINEPREFIX"
        for dll in "${DLLS64[@]}"; do
            uninstall_dll "$dll" "$SYS32"
        done
        for dll in "${DLLS32[@]}"; do
            uninstall_dll "$dll" "$SYSWOW64"
        done
        echo "${green}DXVK 已卸载${reset}"
        ;;
    *)
        cat <<EOF
用法:
  $0 install   [--with-wine /path/to/wine]   # 安装
  $0 uninstall [--with-wine /path/to/wine]   # 卸载
环境变量:
  WINEPREFIX   Wine prefix 目录 (默认: ~/.wine)
  WINE         wine 可执行文件 (默认: wine)
示例:
  WINEPREFIX=~/.wine-hangover ./setup_dxvk.sh install --with-wine ./wine
EOF
        ;;
esac
