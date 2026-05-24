# Logcat Viewer

跨平台 Android logcat 可视化工具，将 Android Studio 导出的 JSON 格式 `.logcat` 文件解析为带颜色高亮的表格，支持过滤、排序、导出 Excel 等功能。

## 特性

- **拖拽打开** — 支持拖放 `.logcat` 文件到窗口
- **级别着色** — V/D/I/W/E/F 按级别自动着色，与 logcat2excel.py 颜色方案一致
- **实时过滤** — 按 Level 多选、Tag/Message 关键词搜索、PID/TID 精确匹配
- **列排序** — 点击表头按任意列排序
- **详情面板** — 选中行后在底部展示完整 Message
- **设备信息** — 侧边栏展示设备型号、Android 版本等元数据
- **统计概览** — 状态栏显示总数、各级别计数
- **导出 Excel** — 一键导出高亮 Excel（与 logcat2excel.py 输出一致）
- **暗色模式** — 支持手动切换，自动检测系统主题
- **跨平台** — macOS / Windows / Linux 原生体验

## 安装

```bash
cd logcat-viewer
pip install -e ".[all]"
```

或直接安装依赖：

```bash
pip install PySide6 openpyxl
```

## 使用

### GUI 模式

```bash
# 启动空白窗口
python -m logcat_viewer

# 启动并直接打开文件
python -m logcat_viewer path/to/file.logcat
```

### CLI 模式（不启动 GUI，直接导出 Excel）

```bash
python -m logcat_viewer --cli input.logcat
python -m logcat_viewer --cli input.logcat output.xlsx
```

## 快捷键

| 快捷键 | 功能 |
|--------|------|
| `Ctrl/Cmd+O` | 打开文件 |
| `Ctrl+Shift+E` | 导出 Excel |
| `Ctrl+Shift+T` | 切换暗色模式 |
| `Ctrl/Cmd+C` | 复制选中行 |
| `Ctrl/Cmd+Q` | 退出 |

## 打包为独立可执行文件

```bash
pip install pyinstaller

# macOS
pyinstaller --onefile --windowed --name "Logcat Viewer" logcat_viewer/main.py

# Windows
pyinstaller --onefile --windowed --name "LogcatViewer" logcat_viewer/main.py

# Linux
pyinstaller --onefile --windowed --name "logcat-viewer" logcat_viewer/main.py
```

## 项目结构

```
logcat-viewer/
├── logcat_viewer/
│   ├── __init__.py              # 版本信息
│   ├── main.py                  # 入口（GUI + CLI）
│   ├── parser.py                # 日志解析模块
│   ├── exporter.py              # Excel 导出模块
│   ├── utils.py                 # 平台适配、主题
│   ├── models/
│   │   └── logcat_model.py      # QAbstractTableModel 数据模型
│   └── widgets/
│       ├── main_window.py       # 主窗口
│       ├── log_table.py         # 日志表格 + 过滤代理
│       ├── filter_bar.py        # 过滤栏
│       ├── device_panel.py      # 设备信息面板
│       ├── detail_panel.py      # 详情面板
│       └── stats_bar.py         # 统计栏
├── pyproject.toml
├── requirements.txt
└── README.md
```

## 兼容性

| 平台 | 状态 |
|------|------|
| macOS | ✅ 支持 |
| Windows | ✅ 支持 |
| Linux | ✅ 支持 |

## License

MIT
