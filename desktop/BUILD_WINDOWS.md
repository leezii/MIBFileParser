# Windows 桌面应用构建指南

本文档说明如何在 Windows 系统上构建 MIB Parser 桌面应用。

## 系统要求

- Windows 10 或更高版本（64位）
- Python 3.12 或更高版本
- Git

## 构建步骤

### 1. 安装依赖工具

#### 安装 Python

从 [python.org](https://www.python.org/downloads/) 下载并安装 Python 3.12+。

安装时请勾选：
- ✅ Add Python to PATH
- ✅ Install for all users（可选）

#### 安装 UV（推荐的 Python 包管理器）

打开 PowerShell 或命令提示符，运行：

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

或使用 pip 安装：

```powershell
pip install uv
```

### 2. 克隆仓库

```powershell
git clone <repository-url>
cd MIBFileParser
```

### 3. 安装项目依赖

```powershell
# 安装项目依赖和桌面应用依赖
uv sync --extra desktop
```

### 4. 构建桌面应用

#### 方式一：使用构建脚本（推荐）

```powershell
cd desktop
uv run python build.py
```

构建脚本会：
- 自动检测平台
- 清理旧的构建文件
- 使用 PyInstaller 打包应用
- 生成可执行文件

#### 方式二：直接使用 PyInstaller

```powershell
cd desktop
uv run python -m PyInstaller build.spec
```

### 5. 查找构建产物

构建完成后，可执行文件位于：

```
desktop/dist/MIBParser/
├── MIBParser.exe          # 主可执行文件
├── _internal/             # 依赖文件和资源
│   ├── *.dll              # Python 扩展 DLL
│   ├── *.pyd              # Python 动态模块
│   ├── src/               # Flask 应用源代码
│   ├── storage/           # 存储资源
│   └── ...
└── MIBParser.exe.manifest # 应用清单
```

### 6. 运行应用

直接双击 `MIBParser.exe` 或从命令行运行：

```powershell
cd desktop\dist\MIBParser
.\MIBParser.exe
```

应用会：
1. 自动寻找可用端口（49152-65535 范围）
2. 在后台启动 Flask 服务器
3. 打开桌面窗口显示 Web 界面

首次运行时，应用会在用户目录创建数据文件夹：

```
C:\Users\<你的用户名>\.mibparser\
├── output/        # 输出文件
├── mib/           # MIB 文件
├── storage/       # 存储资源
└── desktop.log    # 应用日志
```

## 高级选项

### 单文件可执行（One-File）

如果需要打包成单个 .exe 文件（体积会更大），修改 `build.spec`：

找到 Windows 部分（`elif is_windows:`），修改为：

```python
elif is_windows:
    # Single-file executable
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        [],
        name='MIBParser',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        icon=str(DESKTOP_ROOT / 'icons' / 'icon.ico'),
    )
```

注意：单文件模式启动速度较慢，因为需要先解压到临时目录。

### 显示控制台（调试用）

开发或调试时，可以显示控制台窗口查看日志：

修改 `build.spec` 中的 `console=False` 为 `console=True`。

### 添加版本信息

在 `build.spec` 的 Windows 部分添加版本信息：

```python
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='MIBParser',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    version='version_info.txt',  # 添加版本信息文件
    ...
)
```

创建 `version_info.txt`：

```
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1, 0, 0, 0),
    prodvers=(1, 0, 0, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'Your Company'),
        StringStruct(u'FileDescription', u'MIB File Parser and Viewer'),
        StringStruct(u'FileVersion', u'1.0.0.0'),
        StringStruct(u'InternalName', u'MIBParser'),
        StringStruct(u'LegalCopyright', u'Copyright © 2025'),
        StringStruct(u'OriginalFilename', u'MIBParser.exe'),
        StringStruct(u'ProductName', u'MIB Parser'),
        StringStruct(u'ProductVersion', u'1.0.0.0')])
      ]),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
```

## 故障排除

### 问题：端口被占用

如果看到 "Address already in use" 错误，应用会自动尝试其他端口。

手动指定端口范围：修改 `desktop/app.py` 中的 `find_available_port()` 函数。

### 问题：杀毒软件阻止

某些杀毒软件可能会误报 PyInstaller 打包的程序。

解决方法：
1. 添加排除目录到杀毒软件
2. 对可执行文件进行代码签名（需要代码签名证书）

### 问题：缺少 Visual C++ 运行库

应用需要 Visual C++ Redistributable：

下载安装：[Microsoft Visual C++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe)

### 问题：应用启动缓慢

首次启动时，Python 需要解压所有依赖到临时目录。

后续启动会快很多（因为 Windows 有文件缓存）。

## 创建安装程序（可选）

### 使用 Inno Setup

1. 下载安装 [Inno Setup](https://jrsoftware.org/isdl.php)

2. 创建安装脚本 `installer.iss`：

```iss
[Setup]
AppName=MIB Parser
AppVersion=1.0.0
DefaultDirName={pf}\MIBParser
DefaultGroupName=MIB Parser
OutputDir=installer
OutputBaseFilename=MIBParser-Setup
Compression=lzma2
SolidCompression=yes

[Files]
Source: "dist\MIBParser\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\MIB Parser"; Filename: "{app}\MIBParser.exe"
Name: "{commondesktop}\MIB Parser"; Filename: "{app}\MIBParser.exe"

[Run]
Filename: "{app}\MIBParser.exe"; Description: "Launch MIB Parser"; Flags: nowait postinstall skipifsilent
```

3. 编译安装程序：

```powershell
iscc installer.iss
```

## 分发

### 文件夹分发

直接分发 `desktop/dist/MIBParser/` 文件夹，用户运行 `MIBParser.exe`。

### ZIP 压缩包

```powershell
cd desktop/dist
Compress-Archive -Path MIBParser -DestinationPath MIBParser-Windows-x64.zip
```

### 安装程序

使用 Inno Setup 或 NSIS 创建安装程序，提供更好的用户体验。

## 性能优化

### 使用 UPX 压缩

UPX 可以减小可执行文件大小（已在 build.spec 中启用）。

下载 UPX：https://upx.github.io/

### 排除不必要的模块

在 `build.spec` 的 `excludes` 列表中添加不需要的模块：

```python
a = Analysis(
    ...
    excludes=[
        'test',
        'unittest',
        'pydoc',
        ...
    ],
)
```

## 支持的平台

- ✅ Windows 10/11 (64-bit)
- ❌ Windows 7/8/8.1 (未测试，可能不支持)
- ❌ Windows 32-bit (需要修改构建配置)

## 更多信息

- PyInstaller 文档：https://pyinstaller.org/en/stable/
- Python 文档：https://docs.python.org/3/
- 项目仓库：<repository-url>
