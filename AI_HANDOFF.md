# AI Handoff

## 1. Current Goal

当前仓库的实现重心已经从“在应用内完成视频同步”转向“先完成透明遥测图层的生成，再在剪辑软件中手动对齐”。现阶段核心目标是继续稳定这个 overlay-first 的桌面工作流：导入遥测、编辑赛道线与背景图、调整画布组件、导出透明 `MOV ProRes 4444`，并补齐 Windows 分发路径。  
从代码和 README 的真实状态看，主流程已经具备可运行骨架，当前边界不再是“有没有架构”，而是“清理历史分支、收敛 UI/文档、验证打包链路”。  
不确定项：下一优先级究竟是继续做 UI/产品打磨，还是优先完成 Windows 安装包实机验证，仓库内没有主理人最新明确指令。

### 2026-06-11 Phase 4 Update

- Export now uses direct raw-frame piping into `ffmpeg` instead of writing PNG intermediates to disk.
- The active project workflow no longer stores or restores sync state through `ProjectSession`, `ProjectDocument`, `ProjectRepository`, or `ProjectPanel`.
- Export range handling is now fixed to `full_telemetry`, matching the current overlay-first product path.
- Remaining sync-domain helper modules are dormant only; they are no longer part of the active session/export/save-load chain.

### 2026-06-11 Phase 5 Update

- The last active UI copy gaps in the final workflow path have been tightened, including localized preview-time feedback and explicit Chinese confirm/cancel buttons in `ExportDialog`.
- `TrackEditor` no longer accepts the removed `sync_pick` mode through the active API.
- The dormant sync helper modules have now been deleted, so the current repository no longer keeps that compatibility tail in executable code.

### 2026-06-11 Phase 6 Update

- The Windows installer now targets a per-user install location under `{localappdata}\Programs\KartOverlay`, which removes the earlier elevation requirement from smoke verification.
- `packaging/installer.iss` now declares `PrivilegesRequired=lowest`, and the packaging test suite asserts that contract directly.
- Real Windows distribution verification has been rerun successfully across build, portable app launch, silent installer execution, and installed app launch.

## 2. Repository Status

- 2026-06-10 补充：本次已清理工作区中的缓存、构建输出和临时导出目录，当前顶层已不再保留 `build/`、`dist/`、`.pytest_cache/`、`tmp_export_frames/`、`tmp_real_ffmpeg_export/`、`tmp_sync_preview_smoke/`、`tmp_ui_export/`。
- 2026-06-10 补充：递归 `__pycache__/` 目录已清理完成；随后进一步确认 `.superpowers/` 内 pid 均为死进程后，整个 `.superpowers/` 目录也已删除。
- 2026-06-10 补充：`.gitignore` 已追加 `.superpowers/`、`tmp_real_ffmpeg_export/`、`tmp_sync_preview_smoke/`，用于减少后续重复噪声。

- 当前分支：`main`（来自 `git status --short --branch`）。
- `git status` 摘要：
  - 1 个已跟踪文件被修改：`docs/superpowers/specs/2026-06-09-track-visual-feedback-and-windows-packaging-design.md`
  - 存在大量未跟踪文件，包括：`README.md`、`requirements.txt`、`.gitignore`、`.env.local.example`、`kart_overlay/`、`packaging/`、`scripts/`、`tests/`、`docs/superpowers/plans/`、多个设计文档、样例数据和临时输出目录。
- 是否存在未提交修改：是。
- 是否存在未跟踪文件：是，且数量较多。
- 当前工作区是否干净：否。
- 备注：
  - 当前仓库并不是“少量增量修改”，而是“只有少量已跟踪 diff，但主体应用代码仍未加入版本控制”的状态。
  - `git diff` 只显示了一个已跟踪设计文档的增量更新；大量核心代码因尚未跟踪，不会出现在 `git diff` 中。

## 3. Modified Files

以下仅列出已核查到的关键文件与模块，完整未跟踪列表以 `git status` 为准。

### 已跟踪变更

- `docs/superpowers/specs/2026-06-09-track-visual-feedback-and-windows-packaging-design.md`：新增了一段 `Incremental Update 2026-06-09`，把实现状态补充到设计文档中；这说明设计文档仍在被当作演进记录使用，后续更新文档时不要粗暴覆盖历史内容。

### 仓库根目录与说明文件

- `README.md`：当前最完整的进度总览，记录了从架构骨架、遥测导入、赛道编辑、画布、导出、打包，到 2026-06-10 results-first 布局的连续增量状态；后续接手时应先对照它和实际代码是否继续一致。
- `requirements.txt`：定义当前 Python 依赖（`pytest`、`numpy`、`pandas`、`gpxpy`、`PySide6`、`pyinstaller`）；影响本地验证、GUI 运行和打包。
- `.gitignore`：当前忽略了 `build/`、`dist/`、部分缓存和局部导出目录，但没有覆盖 `.superpowers/`、`tmp_real_ffmpeg_export/`、`tmp_sync_preview_smoke/`、样例数据等，导致工作区噪声偏大。
- `.env.local.example`：提供本地环境变量示例；真实 `.env.local` 已存在但未跟踪，属于本地配置边界。

### 应用入口与共享状态

- `kart_overlay/ui/main_window.py`：当前主窗口只保留左侧 `ProjectPanel` 和中间标签页区域，标签页为 `Track / Canvas / Export`；说明旧的独立状态列和旧同步页已不在主壳层。
- `kart_overlay/application/project_session.py`：集中维护遥测、视频、赛道定义、分析结果、组件布局和导出设置，是跨页面共享状态的核心边界；后续改动如果破坏这里，影响范围会直接波及整个工作流。
- `kart_overlay/domain/project.py`：项目文档结构定义，仍保留 `sync` 字段；这与当前“移除主同步流程”的方向形成了历史兼容层。

### 项目导入/保存/加载

- `kart_overlay/ui/project_panel.py`：负责导入遥测、导入视频、保存项目、加载项目；会把背景图路径、赛道定义、组件布局、导出设置写入项目文件，并在加载时重新导入遥测和视频。
- `kart_overlay/infrastructure/persistence/project_repository.py`：使用 JSON 持久化 `ProjectDocument`，实际写入边界较清晰；影响项目文件的稳定性和兼容性。

### 赛道编辑与分析

- `kart_overlay/ui/track_workspace.py`：当前赛道页是 results-first 布局，包含结果面板、编辑器和底部操作条；负责把编辑器分析结果回写到共享 session。
- `kart_overlay/ui/track_editor.py`：实现背景图加载、起终线/分段线编辑、拖拽端点、实时重算、背景固定/轨迹层变换、缩放和平移，是当前业务最敏感的 UI 逻辑文件之一。
- `kart_overlay/ui/track_results_panel.py`、`kart_overlay/ui/track_inspector_panel.py`：承载圈速、分段和状态信息展示；影响当前“结果优先”的交互方向。
- `kart_overlay/domain/timing/*.py`：圈速、分段、穿线和分析汇总逻辑；这些模块当前已有测试覆盖，属于稳定核心。
- `kart_overlay/domain/track/models.py`：定义 `DisplayTransform`、`TimingLine`、`SectorLine`、`TrackDefinition`；当前 transform 语义与旧设计稿存在历史切换，需要谨慎维护。

### 画布与组件渲染

- `kart_overlay/ui/canvas_workspace.py`：实现组件列表、坐标编辑、启用/禁用、预览时间轴，以及直接在预览面板中拖拽/缩放组件。
- `kart_overlay/widgets/*.py`：当前已有速度、计时、海拔、航向、G 值、圈速摘要、最佳圈、分段状态、坐标、小地图等组件；影响预览和最终导出的一致性。
- `kart_overlay/infrastructure/render/frame_renderer.py`：Qt 向量渲染出口；如果未来预览和导出出现不一致，这里是关键排查点。

### 导出与视频信息

- `kart_overlay/ui/export_workspace.py`：当前导出页已实现视频元数据读取、工具状态展示、导出预检、后台导出、进度、取消和日志预览；业务导出目标固定为透明 `MOV`。
- `kart_overlay/application/export_service.py`、`export_task_runner.py`、`export_events.py`：导出编排和后台任务层。
- `kart_overlay/infrastructure/render/ffmpeg_exporter.py`、`export_manifest.py`：生成 `ffmpeg` 编码命令和导出 manifest；影响最终交付资产格式。
- `kart_overlay/infrastructure/video/ffprobe_service.py`：读取视频尺寸、旋转和 FPS；README 已说明这里做过 Windows/编码兼容性加固。

### 打包与 Windows 路径

- `scripts/build_windows_dist.py`：当前 Windows 打包总入口；会调用 PyInstaller、复制 `ffmpeg/ffprobe`、复制 Conda 运行时 DLL、调用 Inno Setup、输出 zip。
- `packaging/kart_overlay.spec`、`packaging/installer.iss`：分别定义 PyInstaller 打包和 Inno Setup 安装器；这条链路存在，但本次未重新执行。
- `kart_overlay/app_paths.py`、`kart_overlay/packaging.py`：定义 `%LOCALAPPDATA%`、`Documents\KartOverlay Projects`、打包运行时工具目录等路径策略；影响安装版和开发态的行为边界。

### 测试与样例

- `tests/unit/*.py`：当前存在 123 个通过的单元测试，覆盖导入、分析、UI、导出、打包路径、项目 roundtrip 等关键模块。
- `test.gpx`、`test.vbo`：仓库内样例遥测文件；测试与手工验证依赖它们，修改会影响回归结果。
- `tmp_real_ffmpeg_export/`、`tmp_sync_preview_smoke/`：临时/验证产物目录，不应手工修改业务内容。

## 4. Completed Work

- 2026-06-11 补充：`Phase 3` 已开始落地，当前范围只覆盖 Canvas 侧组件可见性语义、尺寸标注和相关文案收口，没有进入导出基础设施或 sync 清理。
- 2026-06-11 补充：`CanvasWorkspace` 现在新增 `隐藏组件` 按钮，语义是把当前组件写成 `enabled=False`，不会删除布局数据。
- 2026-06-11 补充：Canvas 左侧勾选语义已收口为 `显示组件`，和底层 `enabled` 状态保持一致，避免“按钮文案和实际行为相反”。
- 2026-06-11 补充：`CanvasPreviewWidget` 现在会在预览画布边缘绘制尺寸边框与宽高标注。
- 2026-06-11 补充：导出桥接已验证继续按 `enabled` 过滤隐藏组件，因此本轮没有引入额外兼容层。
- 2026-06-11 补充：`Phase 2` 已开始落地，当前范围只覆盖 Track 侧交互和结果面板，没有进入 Canvas、sync 清理或 ffmpeg 管道重构。
- 2026-06-11 补充：`TrackEditor` 现在在起终线/分段线首点之后会显示跟随鼠标移动的预览线，并在交互式两点成线后自动回到 `view` 模式。
- 2026-06-11 补充：`TrackWorkspace` 已新增逐点轨迹滑条、当前点索引标签、当前圈号标签，以及更细的平移/缩放/旋转微调按钮。
- 2026-06-11 补充：`TrackResultsPanel` 已新增可滚动圈速列表，并且会跟随当前选中轨迹点同步圈选择。
- 2026-06-11 补充：当前 timing domain 仍未提供显式“无效圈”标记，因此本轮只先把全量圈速列表和当前圈联动做完，未实现基于 invalid flag 的弱化样式。
- 2026-06-11 补充：`Phase 1` 已开始落地，当前只实现导入流程和导出文件命名状态，没有提前进入 track 交互或 ffmpeg 管道重构。
- 2026-06-11 补充：`ProjectPanel` 现在改为“选中文件后直接导入”，遥测和视频都去掉了额外导入按钮；重复选择同一路径也会重新导入。
- 2026-06-11 补充：项目流程面板新增遥测/视频导入进度条，当前实现是轻量级同步进度反馈，不是独立后台导入任务。
- 2026-06-11 补充：`ExportWorkspace` 新增导出目录选择和自定义文件名输入，导出时会把文件名规范化为 `.mov`，并把该状态写回 `ProjectSession.export_settings`。
- 2026-06-11 补充：项目保存/加载的 export roundtrip 已扩展到 `output_filename`，对应定向 pytest 已通过。

- 已完成一次安全范围内的工作区清理，只删除了缓存、构建产物、工具会话残留和临时导出目录，没有删除源码、文档、样例数据或本地环境文件。
- 已递归清理 `kart_overlay/`、`scripts/`、`tests/` 下的全部 `__pycache__/` 目录，减少了当前工作区噪声。
- 已删除 `.superpowers/` 会话残留目录，并把相关忽略规则补入 `.gitignore`，减少后续无关未跟踪文件反复出现。

- 已建立完整的 Python/Qt 桌面应用目录结构，包含 `ui / application / domain / infrastructure / widgets` 分层，且入口可定位到 `kart_overlay/ui/main_window.py` 与 `kart_overlay/main.py`。
- 已实现 GPX/VBO 导入主路径，README 与测试显示样例 `test.gpx`、`test.vbo` 已接入真实解析链路，统一归一化为 `TelemetryStore`。
- 已实现赛道定义与计时分析基础能力，包括起终线、分段线、圈速、分段结果、最佳圈与分析汇总，对应 `kart_overlay/domain/timing/` 与 `kart_overlay/ui/track_editor.py`。
- 已实现赛道编辑页的 results-first 布局，包含顶部结果/编辑双栏和底部操作条；说明“结果优先 + 可拖拽布局”的 UI 方向已经落地到代码。
- 已完成本地背景图工作流，支持导入、替换、清除、透明度调整、持久化背景图路径，并把 `DisplayTransform` 用于轨迹层对齐。
- 已实现画布编辑器与矢量预览，支持组件启停、位置/尺寸修改、直接拖拽与缩放；当前组件集已超过 README 中列举的最小值。
- 已实现透明 MOV 导出工作流，包括视频元数据读取、导出预检、后台任务、进度、取消、日志和 manifest 写出；当前 UI 暴露的最终导出格式为 `mov_prores_4444`。
- 已实现项目保存/加载，能保存并恢复遥测路径、视频路径、赛道定义、背景图路径、组件布局和导出设置；说明当前工作流已经具备“可复用项目文件”的基础闭环。
- 已补入 Windows 分发相关脚本和安装器资源，但本次仅验证了脚本/测试存在，没有重新跑出新的安装包。
- 已执行全量 Python 验证：
  - `D:\Anaconda_env\karting\python.exe -m compileall kart_overlay scripts tests` 通过。
  - `D:\Anaconda_env\karting\python.exe -m pytest -q` 通过，结果为 `123 passed in 54.10s`。

## 5. Key Decisions

- 决策：当前主流程已转为 overlay-first，而不是在应用内完成视频同步。
  - 原因：README 的最新增量更新明确说明旧 `Sync` 页已从主壳层移除，导出统一回到 `full_telemetry`。
  - 影响：`kart_overlay/ui/main_window.py`、`kart_overlay/ui/export_workspace.py`、`ProjectSession`、项目保存逻辑、后续产品文档。
  - 待确认：是否彻底删除遗留的 `sync` 领域模型与保存字段，还是暂时保留兼容壳层。

- 决策：赛道背景图采用本地图片，不再依赖 Amap 或远程底图。
  - 原因：最新 2026-06-10 设计文档明确转向本地背景图，且当前 `track_workspace.py` / `track_editor.py` 已按本地图片工作流实现。
  - 影响：`track_editor` 背景图交互、项目文件中的 `background_image_path`、Windows 安装包分发策略。
  - 待确认：是否还需要彻底清理历史 Amap 相关文件和测试命名。

- 决策：当前轨迹对齐模型采用“固定背景图，移动/缩放/旋转轨迹层”。
  - 原因：`2026-06-10-track-editor-results-first-layout-design.md` 与 `tests/unit/test_track_editor_advanced.py` 都验证了这一最新语义，且 `track_editor.py` 的实现确实如此。
  - 影响：`DisplayTransform` 的语义、赛道编辑交互、项目文件兼容理解、后续文档说明。
  - 待确认：旧的 `2026-06-10-local-background-and-windows-installer-design.md` 仍写的是“移动背景图”，历史文档存在语义冲突，需要后续统一说明。

- 决策：跨页面状态通过 `ProjectSession` 统一传递，而不是页面之间直接互调。
  - 原因：当前已经有遥测、视频、赛道定义、分析结果、组件布局和导出设置的共享信号边界。
  - 影响：主窗口组装方式、项目保存/加载、导出默认值、画布/赛道页联动。
  - 待确认：若后续要清理 sync 历史代码，需要一起评估 `ProjectSession` 中的 sync 字段是否保留。

- 决策：Windows 安装态路径使用 `%LOCALAPPDATA%\KartOverlay` 与 `%USERPROFILE%\Documents\KartOverlay Projects`。
  - 原因：`app_paths.py` 与打包脚本已采用该策略，目的是把安装目录和用户数据目录分离。
  - 影响：安装器脚本、项目默认保存位置、运行时日志/缓存放置位置。
  - 待确认：是否需要再补“首次启动迁移/目录创建”方面的手工烟测。

## 6. Validation

```bash
Get-ChildItem -Recurse -Directory -Filter __pycache__ | Select-Object -ExpandProperty FullName
```

结果：

- 通过；
- 当前无输出，说明工作区内已无残留 `__pycache__/` 目录。

```bash
git status --short --branch
```

结果：

- 通过；
- 清理后已确认 `build/`、`dist/`、`.pytest_cache/`、各类 `tmp_*` 目录以及 `.superpowers/` 均不再出现在工作区顶层。

```bash
Get-ChildItem '.superpowers' -Recurse -Filter 'server.pid' | ForEach-Object { (Get-Content $_.FullName -Raw).Trim() }
```

结果：

- 通过；
- 已读到 3 个历史 pid 值和 1 个空 pid 文件，说明目录内主要是会话残留。

```bash
Get-Process -Id 11960,34984,34096
```

结果：

- 未通过 / 等价确认失败；
- 实际通过 `Get-Process -Id <pid> -ErrorAction SilentlyContinue` 核查后，这 3 个 pid 均不存在，判断为死进程残留，因此 `.superpowers/` 被删除。

```bash
git status --short --branch
```

结果：

- 通过；
- 输出显示当前分支为 `main`，工作区不干净，存在 1 个已跟踪修改和大量未跟踪文件。

```bash
git diff --stat
```

结果：

- 通过；
- 仅显示 `docs/superpowers/specs/2026-06-09-track-visual-feedback-and-windows-packaging-design.md` 有 12 行新增、1 行删除。

```bash
git diff
```

结果：

- 通过；
- 已核实唯一 tracked diff 为上述设计文档的增量更新。

```bash
pytest -q
```

结果：

- 失败；
- 报错摘要：当前 shell 的 `PATH` 中没有 `pytest`，PowerShell 返回 `pytest is not recognized as the name of a cmdlet...`。

```bash
python -m compileall kart_overlay scripts tests
```

结果：

- 失败；
- 现象：当前 shell 默认 `python` 入口不可用，未得到有效编译结果；后续改用显式解释器执行。

```bash
D:\Anaconda_env\karting\python.exe -m compileall kart_overlay scripts tests
```

结果：

- 通过；
- 已成功遍历并编译 `kart_overlay`、`scripts`、`tests`。

```bash
D:\Anaconda_env\karting\python.exe -m pytest -q
```

结果：

- 通过；
- 输出摘要：`123 passed in 54.10s`。

## 7. Known Issues

- 问题：仓库工作区噪声较大，主体应用代码和测试当前仍未加入版本控制。

  - 现象：`git status` 显示 `kart_overlay/`、`packaging/`、`scripts/`、`tests/`、`README.md` 等大量未跟踪文件。
  - 依据：已执行 `git status --short --branch`。
  - 当前判断：这不是单一文件遗漏，而是整个项目主体尚未进入 Git 跟踪的状态；后续提交时极易混入无关内容。
  - 下一步建议：先明确“哪些目录应进入版本控制、哪些应忽略”，再分批整理提交。

- 问题：同步功能在 UI 层已被移出主流程，但 sync 领域模型和项目字段仍然保留。

  - 现象：主窗口只有 `Track / Canvas / Export`，但 `ProjectSession`、`ProjectDocument`、`ProjectPanel`、`tests/unit/test_sync_model.py` 仍保留 sync 相关结构。
  - 依据：`kart_overlay/ui/main_window.py`、`kart_overlay/application/project_session.py`、`kart_overlay/domain/project.py`、`kart_overlay/ui/project_panel.py`。
  - 当前判断：当前不是崩溃级问题，但属于历史分支残留，容易让后续接手者误以为 sync 仍是主路径。
  - 下一步建议：由主理人确认是否彻底清理 sync 残留；若暂时保留，需要在 README 和项目 schema 中明确说明用途。

- 问题：UI 中文化不彻底，部分赛道编辑页控件仍为英文硬编码。

  - 现象：`TrackWorkspace` 中存在 `Import Background`、`Replace Background`、`Clear Background`、`Reset Transform`、`Zoom +`、`Zoom -`、分组标题 `Mode / Background / Track Adjust / Line Actions` 等硬编码英文。
  - 依据：`kart_overlay/ui/track_workspace.py`。
  - 当前判断：功能不受影响，但与 README 中“中国化产品 UI”描述不完全一致。
  - 下一步建议：如果下一阶段做产品 polish，应统一收口到 `ui/texts.py` 文本边界。

- 问题：有一条通过中的测试没有真正验证“缩小后 scale 恢复”。

  - 现象：`tests/unit/test_track_workspace.py` 末尾断言为 `assert workspace.editor.display_transform.scale <= workspace.editor.display_transform.scale`，该断言恒为真。
  - 依据：已检查测试文件源码。
  - 当前判断：这是测试质量问题，不代表业务一定有 bug，但它削弱了对 `precise_zoom_out_button` 的回归保护。
  - 下一步建议：修正为和点击前或放大后的 scale 做对比，再重跑相关测试。

- 问题：历史设计文档对 `DisplayTransform` 语义存在冲突。

  - 现象：`2026-06-10-local-background-and-windows-installer-design.md` 仍描述“移动背景图”，而 `2026-06-10-track-editor-results-first-layout-design.md` 与代码实现已经转为“固定背景、移动轨迹层”。
  - 依据：已阅读两份设计文档，并核对 `track_editor.py` 与 `test_track_editor_advanced.py`。
  - 当前判断：当前实现方向明确，但文档历史存在分叉，容易误导后续维护。
  - 下一步建议：后续若更新设计文档，应显式标注旧方案已过期或被新方案替代。

## 8. Risks

- 当前 `.gitignore` 虽已覆盖 `.superpowers/` 和已知临时目录，但仍未覆盖未来可能新增的其他工具状态目录；如果继续使用同类插件，工作区仍可能再出现新噪声。

- 当前最大风险是误提交无关 diff。仓库主体代码、测试、样例和临时目录大量未跟踪，后续若直接 `git add .`，很容易把临时文件、设计文档和业务代码一次性混在一起。
- 打包链路虽有代码和测试覆盖，但本次没有重新执行 `scripts/build_windows_dist.py`，也没有验证 Inno Setup、`ffmpeg/ffprobe`、Conda DLL 在当前机器上的真实可用性；继续推进安装包工作时存在环境风险。
- 当前默认 shell 的 `python` / `pytest` 不可直接使用，必须依赖显式解释器 `D:\Anaconda_env\karting\python.exe`；如果后续接手者忽略这一点，会误判仓库“无法运行”。
- `DisplayTransform` 的业务语义已经切换，如果后续有人按旧设计稿去改背景图行为，可能会直接破坏当前测试通过的轨迹对齐模型。
- 项目文件会保存外部背景图路径；跨机器、移动目录或清理素材时，用户已有项目可能丢失背景图引用，尽管赛道线本身不会丢。
- 当前导出依赖 Qt 向量渲染 + FFmpeg 编码双路径；如果后续只改预览组件、不改导出组件构建，可能出现“画布预览正常、导出内容不一致”的回归。
- 仓库当前明显偏向 Windows 路径与安装器，跨平台运行没有承诺；若后续在非 Windows 环境继续开发，需要特别注意路径和打包假设。

## 9. Remaining Work

- [ ] 待办事项：确认是否保留 sync 相关领域模型、项目字段和测试。

  - 依赖条件：主理人确认“未来是否还会恢复应用内同步功能”。
  - 建议处理方式：先用 `rg -n "sync_model|SyncState|sync_service|sync_offset" kart_overlay tests` 做范围盘点，再决定保留兼容层还是整体清理。
  - 优先级：高。

- [ ] 待办事项：整理版本控制边界，减少当前未跟踪噪声。

  - 依赖条件：先区分“应纳入仓库的源码/测试/说明文件”和“应忽略的临时产物/本地状态”。
  - 建议处理方式：补充 `.gitignore` 或分批 `git add`，避免一次性引入无关目录。
  - 优先级：高。

- [ ] 待办事项：修正 `tests/unit/test_track_workspace.py` 中的无效缩放断言。

  - 依赖条件：无。
  - 建议处理方式：把 zoom-out 断言改为和点击前或 zoom-in 后的数值比较，再跑定向测试。
  - 优先级：中。

- [ ] 待办事项：决定 UI 文案是否继续统一中文化。

  - 依赖条件：确认当前阶段是功能收尾还是产品 polish。
  - 建议处理方式：优先把 `TrackWorkspace` 中硬编码英文迁移到 `ui/texts.py`，避免多语言边界继续分散。
  - 优先级：中。

- [ ] 待办事项：重新执行 Windows 打包烟测。

  - 依赖条件：当前机器已安装 Inno Setup，并提供可用的 `ffmpeg/ffprobe` 与 Conda 运行时 DLL。
  - 建议处理方式：用显式解释器运行 `scripts/build_windows_dist.py`，再检查 `dist/` 产物是否齐全且可启动。
  - 优先级：高。

## 10. Next Step

1. 先执行 `rg -n "sync_model|SyncState|sync_service|sync_offset" kart_overlay tests`，盘点遗留 sync 边界到底还有哪些文件。
2. 打开 `tests/unit/test_track_workspace.py`，修正 `precise_zoom_out_button` 的无效断言。
3. 用 `D:\Anaconda_env\karting\python.exe -m pytest tests/unit/test_track_workspace.py tests/unit/test_track_editor_advanced.py -q` 重跑赛道编辑相关回归。
4. 如果主理人确认不再需要应用内同步，再清理 `ProjectSession`、`ProjectDocument`、`ProjectPanel` 中对应残留。
5. 完成任何改动后，重新更新本文件。

## 11. Do Not Touch

- `.env.local`：本地运行环境配置，当前未跟踪，不应在没有明确需求时修改或提交。
- `test.gpx`、`test.vbo`：当前测试和手工验证依赖的样例数据，除非是有意更新 fixture，否则不要改。
- `tmp_real_ffmpeg_export/`、`tmp_sync_preview_smoke/`：临时导出/烟测产物目录，不应手工编辑业务内容。
- `docs/superpowers/specs/*.md` 与 `docs/superpowers/plans/*.md`：这些文件兼具历史记录和当前参考作用，更新时应增量追加或显式标注过期，不要粗暴重写历史。
- `kart_overlay/domain/timing/*.py`：当前已被全量测试覆盖且属于计时核心，除非有明确缺陷或需求，不要顺手重构。

## 12. Suggested Verification Commands

```bash
git status --short --branch
D:\Anaconda_env\karting\python.exe -m compileall kart_overlay scripts tests
D:\Anaconda_env\karting\python.exe -m pytest -q
D:\Anaconda_env\karting\python.exe -m pytest tests/unit/test_track_workspace.py tests/unit/test_track_editor_advanced.py -q
$env:KART_OVERLAY_INNO_SETUP_PATH='C:\Path\To\ISCC.exe'; D:\Anaconda_env\karting\python.exe scripts\build_windows_dist.py
```

## 13. Handoff Summary

本次还额外完成了一轮工作区清理：已删除缓存、构建输出、临时导出目录、`.superpowers/` 会话残留和全部 `__pycache__/`，但没有动源码、样例数据和本地环境文件。  
为避免同类噪声反复出现，`.gitignore` 已补充 `.superpowers/`、`tmp_real_ffmpeg_export/`、`tmp_sync_preview_smoke/`。  
当前仓库已经不是“空壳原型”，而是一个拥有真实 Qt 界面、遥测导入、赛道编辑、画布编辑、透明 MOV 导出、项目保存/加载和 Windows 打包脚本的完整工作流雏形。  
本次核查确认：当前分支是 `main`，工作区不干净，只有 1 个 tracked 文档有 diff，但主体源码和测试大量处于未跟踪状态。  
最新实现方向已经从“应用内同步”收敛到“overlay-first 导出”，并采用“固定背景图、移动轨迹层”的赛道对齐模型。  
本次没有改业务代码，只新增本交接文档；验证方面，显式解释器下 `compileall` 通过，`pytest` 全量通过，结果为 `123 passed in 54.10s`。  
当前最重要的风险不是单个功能崩溃，而是版本控制边界混乱、sync 历史残留、打包链路尚未重新烟测。  
如果下一位接手者继续推进，建议先从 sync 残留盘点和无效测试断言修正开始，再决定是否进入打包实测或 UI 文案收尾。  
另外，更新设计/交接文档时应保留历史增量，不要把旧设计直接覆盖掉，因为当前 docs 仍承担实现演进记录的作用。
