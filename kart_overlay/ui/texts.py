_APP_TEXTS: dict[str, str] = {
    "window_title": "卡丁车数据叠层",
    "app_name": "卡丁车数据叠层",
    "tab_track": "赛道编辑",
    "tab_canvas": "画布编辑",
    "tab_export": "导出视频",
    "project_workflow": "项目流程",
    "telemetry_file": "遥测文件",
    "video_file": "视频文件",
    "telemetry_not_loaded": "遥测：未导入",
    "video_not_loaded": "视频：未导入",
    "project_not_loaded": "项目：未加载",
    "browse_telemetry": "选择遥测文件",
    "browse_video": "选择视频文件",
    "save_project": "保存项目",
    "load_project": "加载项目",
    "select_telemetry_file": "选择遥测文件",
    "select_video_file": "选择视频文件",
    "save_project_dialog": "保存项目",
    "load_project_dialog": "加载项目",
    "project_file_filter": "卡丁车叠层项目 (*.kartoverlay);;所有文件 (*)",
    "telemetry_file_filter": "遥测文件 (*.gpx *.vbo);;所有文件 (*)",
    "video_file_filter": "视频文件 (*.mp4 *.mov *.mkv *.avi);;所有文件 (*)",
    "read_video_info": "读取视频信息",
    "tools_status_ffmpeg_ready": "FFmpeg：已就绪",
    "tools_status_ffmpeg_missing": "FFmpeg：缺失",
    "tools_status_ffprobe_ready": "FFprobe：已就绪",
    "tools_status_ffprobe_missing": "FFprobe：缺失",
    "video_info_not_loaded": "视频：未读取",
    "view_mode": "查看轨迹",
    "start_finish_mode": "新增起终线",
    "sector_mode": "新增分段线",
    "lap_crossings": "过线次数",
    "lap_count": "圈数",
    "last_lap": "上一圈",
    "best_lap": "最快圈",
    "sectors": "分段",
    "last_sector_times": "最近分段",
    "best_sector_times": "最佳分段",
    "workflow_status_telemetry": "遥测",
    "workflow_status_video": "视频",
    "workflow_status_not_loaded": "未导入",
    "canvas_widgets": "画布组件",
    "canvas_preview": "预览",
    "apply_position": "应用位置",
    "position_empty": "位置：-",
    "canvas_preview_title": "画布组件预览",
    "preview_time_default": "预览时间：0.000 秒",
    "preview_time_value": "预览时间：{seconds:.3f} 秒",
    "preview_summary_empty": "暂无组件摘要",
    "export_dialog_title": "导出叠层",
    "export_format": "导出格式",
    "export_format_mov_alpha": "MOV ProRes 4444（透明）",
    "fps": "帧率",
    "output_path": "输出路径",
    "output_directory": "输出目录",
    "canvas_width": "画布宽度",
    "canvas_height": "画布高度",
    "range_mode_full_telemetry": "完整遥测区间",
    "preflight_waiting": "预检：等待导出参数",
    "status_ready": "就绪",
    "export_mov": "导出 MOV",
    "cancel_export": "取消导出",
    "browse_output_directory": "选择目录",
    "select_output_directory": "选择导出目录",
    "output_filename": "文件名",
    "widget_visible": "显示组件",
    "hide_widget": "隐藏组件",
    "dialog_ok": "确定",
    "dialog_cancel": "取消",
    "background_not_loaded": "背景图：未加载",
    "background_loaded": "背景图：{name}",
    "background_load_failed": "背景图加载失败：{name}",
    "no_selected_sector_line": "当前没有选中的分段线",
    "only_sector_lines_deletable": "仅支持删除分段线",
    "start_finish_reset_done": "起终线已重置",
}

_WIDGET_DISPLAY_NAMES: dict[str, str] = {
    "speed": "速度",
    "timer": "当前圈",
    "altitude": "海拔",
    "heading": "航向",
    "g_force": "G 值",
    "lap_summary": "圈速摘要",
    "best_lap": "最快圈",
    "sector_state": "分段状态",
    "coordinates": "坐标",
    "mini_track": "赛道图",
}

_DISPLAY_NAME_TO_WIDGET_KEY: dict[str, str] = {
    display_name: widget_key for widget_key, display_name in _WIDGET_DISPLAY_NAMES.items()
}

_TRACK_MODE_DISPLAY_NAMES: dict[str, str] = {
    "view": _APP_TEXTS["view_mode"],
    "start_finish": _APP_TEXTS["start_finish_mode"],
    "sector": _APP_TEXTS["sector_mode"],
}

_TRACK_LINE_DISPLAY_NAMES: dict[str, str] = {
    "Start/Finish": "起终线",
}

_TRACK_ENDPOINT_DISPLAY_NAMES: dict[str, str] = {
    "start": "起点",
    "end": "终点",
}

_RANGE_MODE_OPTIONS: list[tuple[str, str]] = [
    ("full_telemetry", _APP_TEXTS["range_mode_full_telemetry"]),
]


def app_text(key: str) -> str:
    return _APP_TEXTS.get(key, key)


def widget_display_name(widget_key: str) -> str:
    return _WIDGET_DISPLAY_NAMES.get(widget_key, widget_key)


def widget_key_from_display_name(display_name: str) -> str:
    return _DISPLAY_NAME_TO_WIDGET_KEY.get(display_name, display_name)


def track_mode_display_name(mode: str) -> str:
    return _TRACK_MODE_DISPLAY_NAMES.get(mode, mode)


def track_mode_status(mode: str) -> str:
    return f"当前模式：{track_mode_display_name(mode)}"


def track_line_display_name(name: str) -> str:
    return _TRACK_LINE_DISPLAY_NAMES.get(name, name)


def track_endpoint_display_name(name: str) -> str:
    return _TRACK_ENDPOINT_DISPLAY_NAMES.get(name, name)


def range_mode_options() -> list[tuple[str, str]]:
    return list(_RANGE_MODE_OPTIONS)
