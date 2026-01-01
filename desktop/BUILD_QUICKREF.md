# MIB Parser - 桌面应用快速构建指南

## 🚀 快速开始

### macOS

```bash
# 1. 安装依赖
uv sync --extra desktop

# 2. 构建应用
cd desktop
uv run python build.py --clean

# 3. 运行应用
open dist/MIBParser.app
```

### Windows

```powershell
# 1. 安装 uv
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# 2. 安装依赖
uv sync --extra desktop

# 3. 构建应用
cd desktop
uv run python build.py --clean

# 4. 运行应用
.\dist\MIBParser\MIBParser.exe
```

### Linux

```bash
# 1. 安装依赖
uv sync --extra desktop

# 2. 构建应用
cd desktop
uv run python build.py --clean

# 3. 运行应用
./dist/mib-parser
```

## 📦 构建产物

| 平台 | 位置 | 大小 |
|------|------|------|
| macOS | `desktop/dist/MIBParser.app` | ~40 MB |
| Windows | `desktop/dist/MIBParser/` | ~35 MB |
| Linux | `desktop/dist/mib-parser` | ~30 MB |

## 🔧 开发模式运行

所有平台：

```bash
# 从项目根目录
uv run python desktop/app.py
```

## 📝 详细文档

- **Windows**: [BUILD_WINDOWS.md](BUILD_WINDOWS.md)
- **macOS**: [BUILD_MACOS.md](BUILD_MACOS.md) (待创建)
- **Linux**: [BUILD_LINUX.md](BUILD_LINUX.md) (待创建)

## ⚙️ 系统要求

### macOS
- macOS 10.15 (Catalina) 或更高版本
- Python 3.12+ (开发模式)

### Windows
- Windows 10/11 (64位)
- Visual C++ Redistributable (自动包含)

### Linux
- 任何现代 Linux 发行版
- GTK+ 3 库 (PyWebView 依赖)

## 🐛 故障排除

### macOS: "应用已损坏"

```bash
xattr -cr desktop/dist/MIBParser.app
```

### Windows: 杀毒软件阻止

添加到排除列表或获取代码签名证书。

### Linux: 缺少依赖

```bash
# Ubuntu/Debian
sudo apt-get install python3-gi python3-gi-cairo gir1.2-gtk-3.0

# Fedora
sudo dnf install python3-gobject gtk3

# Arch Linux
sudo pacman -S python-gobject gtk3
```

## 📮 分发

### macOS - DMG

```bash
cd desktop/dist
hdiutil create -volname "MIB Parser" -srcfolder MIBParser.app -ov -format UDZO MIB-Parser.dmg
```

### Windows - ZIP

```powershell
cd desktop/dist
Compress-Archive -Path MIBParser -DestinationPath MIBParser-Windows-x64.zip
```

### Windows - 安装程序（需要 Inno Setup）

```powershell
iscc installer.iss
```

## 🔒 代码签名（可选）

### macOS

```bash
codesign --deep --force --verify --verbose --sign "Developer ID Application: Your Name" dist/MIBParser.app
```

### Windows

使用 SignTool 或第三方服务（如 DigiCert）。

---

**需要帮助？** 查看详细文档或提交 Issue。
