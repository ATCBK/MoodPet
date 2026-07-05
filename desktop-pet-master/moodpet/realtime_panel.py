from pathlib import Path
from typing import Callable, List, Optional, Tuple

from PyQt5.QtCore import QPointF, QRectF, QSize, Qt, QTimer
from PyQt5.QtGui import QColor, QFont, QImage, QMovie, QPainter, QPainterPath, QPen, QPixmap, QPolygonF
from PyQt5.QtWidgets import QComboBox, QFrame, QLabel, QPushButton, QWidget

try:
    import cv2
    from moodpet.emotion_camera import open_camera_capture
except Exception:  # pragma: no cover - OpenCV availability is environment dependent.
    cv2 = None
    open_camera_capture = None

from moodpet.emotion import EmotionState
from moodpet.pixel_icons import apply_button_icon, apply_label_icon
from moodpet.realtime_monitor import (
    build_monitor_rows,
    build_trend_points,
    confidence_percent,
    default_monitor_state,
    preview_badge_text,
)
from moodpet.side_nav import build_pet_sidebar


INK = "#10151b"
NAVY = "#062b36"
TEAL = "#18c7a4"
CREAM = "#fff1da"
BORDER = "#5a432f"
PANEL = "#fff7e9"
PINK = "#ff6374"
MINT = "#19b995"


def label(parent: QWidget, text: str, geometry: Tuple[int, int, int, int], size: int = 13, weight: int = 700) -> QLabel:
    item = QLabel(text, parent)
    item.setGeometry(*geometry)
    item.setStyleSheet(
        f"color: {INK}; border: none; font-family: 'Microsoft YaHei';"
        f"font-size: {size}pt; font-weight: {weight};"
    )
    item.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    return item


class PixelButton(QPushButton):
    def __init__(self, text: str, parent: QWidget, color: str = MINT) -> None:
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        hover_color = QColor(color).lighter(112).name()
        self.setStyleSheet(
            "QPushButton {"
            f"background-color: {color};"
            "color: white;"
            "border: 3px solid #102029;"
            "border-radius: 7px;"
            "font-family: 'Microsoft YaHei';"
            "font-size: 11pt;"
            "font-weight: 900;"
            "padding: 6px 10px;"
            "}"
            f"QPushButton:hover {{ background-color: {hover_color}; }}"
            "QPushButton:pressed { padding-top: 10px; padding-left: 16px; }"
        )


class CameraPreview(QWidget):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.capture = None
        self.active = False
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._read_frame)
        self.setStyleSheet(
            "background-color: #18334b;"
            "border: 3px solid #071927;"
            "border-radius: 4px;"
        )
        self._build_view()

    def set_state(self, state: EmotionState, enabled: bool) -> None:
        self.badge.setText("● " + preview_badge_text(enabled, state))
        self.face_label.setText("当前情绪：" + state.label_zh)

    def _build_view(self) -> None:
        self.image_label = QLabel("等待摄像头画面", self)
        self.image_label.setGeometry(8, 8, 580, 418)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet(
            "background-color: #102943; color: #9ff5d8; border: none;"
            "font-family: 'Microsoft YaHei'; font-size: 15pt; font-weight: 900;"
        )

        self.badge = QLabel("● 摄像头预览中", self)
        self.badge.setGeometry(28, 22, 172, 42)
        self.badge.setStyleSheet(
            "background-color: rgba(11,24,32,225); color: white; border: none; border-radius: 8px;"
            "font-family: 'Microsoft YaHei'; font-size: 11pt; font-weight: 900; padding-left: 12px;"
        )

        self.face_label = QLabel("当前情绪：未知", self)
        self.face_label.setGeometry(206, 374, 190, 34)
        self.face_label.setAlignment(Qt.AlignCenter)
        self.face_label.setStyleSheet(
            "background-color: rgba(11,24,32,210); color: #20f2a9; border: none; border-radius: 6px;"
            "font-family: 'Microsoft YaHei'; font-size: 13pt; font-weight: 900;"
        )

    def start_preview(self, camera_index: int = 0) -> None:
        if self.active:
            return
        if cv2 is None or open_camera_capture is None:
            self.image_label.setText("当前环境缺少 OpenCV，无法打开摄像头")
            return
        self.capture, _ = open_camera_capture(camera_index)
        if self.capture is None or not self.capture.isOpened():
            self.image_label.setText("未读取到摄像头画面")
            self.capture = None
            return
        self.active = True
        self.timer.start(33)

    def stop_preview(self) -> None:
        self.timer.stop()
        self.active = False
        if self.capture is not None:
            self.capture.release()
            self.capture = None
        self.image_label.setPixmap(QPixmap())
        self.image_label.setText("摄像头预览已关闭")

    def _read_frame(self) -> None:
        if self.capture is None:
            self.stop_preview()
            return
        ok, frame = self.capture.read()
        if not ok or frame is None:
            self.image_label.setText("摄像头画面读取失败")
            return
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        height, width, channels = rgb.shape
        image = QImage(rgb.data, width, height, channels * width, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(image.copy()).scaled(
            self.image_label.size(),
            Qt.KeepAspectRatioByExpanding,
            Qt.SmoothTransformation,
        )
        self.image_label.setPixmap(pixmap)

    def closeEvent(self, event) -> None:
        self.stop_preview()
        super().closeEvent(event)


class TrendChart(QWidget):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.points: List[Tuple[str, int]] = build_trend_points(default_monitor_state(), True)

    def set_points(self, points: List[Tuple[str, int]]) -> None:
        self.points = points
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        area = self.rect().adjusted(42, 24, -24, -38)
        painter.fillRect(self.rect(), QColor(PANEL))
        painter.setPen(QPen(QColor("#d8b98e"), 1))
        for step in range(5):
            y = area.top() + step * area.height() / 4
            painter.drawLine(area.left(), int(y), area.right(), int(y))
        for step in range(9):
            x = area.left() + step * area.width() / 8
            painter.drawLine(int(x), area.top(), int(x), area.bottom())

        painter.setPen(QPen(QColor("#7c654d"), 2))
        painter.drawLine(area.left(), area.top(), area.left(), area.bottom())
        painter.drawLine(area.left(), area.bottom(), area.right(), area.bottom())

        painter.setFont(QFont("Microsoft YaHei", 9, QFont.Bold))
        painter.drawText(4, area.top() - 4, "100%")
        painter.drawText(14, area.center().y() + 4, "50%")
        painter.drawText(22, area.bottom() + 4, "0%")

        if len(self.points) < 2:
            return

        coords = []
        for index, (_, value) in enumerate(self.points):
            x = area.left() + index * area.width() / (len(self.points) - 1)
            y = area.bottom() - max(0, min(100, value)) * area.height() / 100
            coords.append(QPointF(x, y))

        fill = QPainterPath()
        fill.moveTo(coords[0].x(), area.bottom())
        for point in coords:
            fill.lineTo(point)
        fill.lineTo(coords[-1].x(), area.bottom())
        fill.closeSubpath()
        painter.fillPath(fill, QColor(42, 190, 132, 54))

        painter.setPen(QPen(QColor(MINT), 4, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawPolyline(QPolygonF(coords))
        painter.setBrush(QColor("#9cf1c9"))
        painter.setPen(QPen(QColor(MINT), 3))
        for point in coords:
            painter.drawEllipse(point, 5, 5)

        painter.setFont(QFont("Microsoft YaHei", 9, QFont.Bold))
        painter.setPen(QColor(INK))
        for index in [0, 2, 4, 6, 8]:
            if index < len(self.points):
                x = area.left() + index * area.width() / (len(self.points) - 1)
                painter.drawText(QRectF(x - 28, area.bottom() + 10, 56, 24), Qt.AlignCenter, self.points[index][0])


class RealtimeMonitorWindow(QWidget):
    def __init__(
        self,
        base_dir: Path,
        get_state: Callable[[], EmotionState],
        is_enabled: Callable[[], bool],
        toggle_recognition: Callable[[], None],
        open_target: Optional[Callable[[str], None]] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.base_dir = base_dir
        self.get_state = get_state
        self.is_enabled = is_enabled
        self.toggle_recognition = toggle_recognition
        self.open_target = open_target or (lambda module_id: None)
        self.row_labels: List[QLabel] = []
        self.row_frames: List[QFrame] = []
        self.setWindowTitle("MoodPet 实时检测")
        self.setFixedSize(1360, 760)
        self.setStyleSheet(f"background-color: {CREAM};")
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        self.sidebar, self.sidebar_items = build_pet_sidebar(self, "realtime", self.open_target)

        label(self, "⌂  ›  功能导航  ›  实时检测", (302, 28, 330, 38), 16, 900)
        self.min_button = PixelButton("－", self, "#58d2bd")
        self.min_button.setGeometry(1220, 26, 34, 34)
        self.min_button.clicked.connect(self.showMinimized)
        self.close_button = PixelButton("", self, PINK)
        self.close_button.setGeometry(1268, 26, 34, 34)
        apply_button_icon(self.close_button, "close", 24)
        self.close_button.clicked.connect(self.hide)

        self.preview = CameraPreview(self)
        self.preview.setGeometry(302, 96, 596, 434)

        controls = QFrame(self)
        controls.setGeometry(302, 532, 596, 76)
        controls.setStyleSheet(f"background-color: {PANEL}; border: 2px solid #b99169; border-radius: 5px;")
        label(controls, "摄像头：", (20, 19, 80, 34), 12, 900)
        self.camera_select = QComboBox(controls)
        self.camera_select.setGeometry(92, 18, 184, 36)
        self.camera_select.addItems(["Integrated Camera", "Mock Camera"])
        self.camera_select.setStyleSheet(
            "QComboBox { background: #fffaf2; border: 2px solid #b99169; border-radius: 5px;"
            "font-family: 'Microsoft YaHei'; font-size: 11pt; font-weight: 700; padding-left: 10px; }"
        )
        self.open_button = PixelButton("打开预览", controls, MINT)
        self.open_button.setGeometry(296, 15, 138, 42)
        apply_button_icon(self.open_button, "camera", 20)
        self.open_button.clicked.connect(self._ensure_open)
        self.close_preview_button = PixelButton("关闭预览", controls, PINK)
        self.close_preview_button.setGeometry(448, 15, 128, 42)
        apply_button_icon(self.close_preview_button, "video", 20)
        self.close_preview_button.clicked.connect(self._ensure_closed)

        self.info_panel = QFrame(self)
        self.info_panel.setGeometry(930, 96, 410, 270)
        self.info_panel.setStyleSheet(f"background-color: {PANEL}; border: 2px solid #b99169; border-radius: 8px;")
        label(self.info_panel, "♥ 实时检测信息", (20, 10, 250, 36), 15, 900)
        row_specs = [(54, 36), (98, 36), (142, 62), (212, 36)]
        for index, (row_y, row_h) in enumerate(row_specs):
            row_frame = QFrame(self.info_panel)
            row_frame.setGeometry(24, row_y, 360, row_h)
            row_frame.setStyleSheet(
                "QFrame { background-color: rgba(255,255,255,70); border: none; border-bottom: 1px solid #d5b58c; }"
            )
            row_label = QLabel(row_frame)
            row_label.setGeometry(8, 0, 340, 32)
            row_label.setStyleSheet(
                "color: #111318; border: none; font-family: 'Microsoft YaHei';"
                "font-size: 11pt; font-weight: 900;"
            )
            row_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.row_frames.append(row_frame)
            self.row_labels.append(row_label)

        self.confidence_bar = QFrame(self.row_frames[2])
        self.confidence_bar.setGeometry(150, 38, 196, 14)
        self.confidence_bar.setStyleSheet("background-color: #fffaf2; border: 2px solid #8d6c4c; border-radius: 7px;")
        self.confidence_fill = QFrame(self.confidence_bar)
        self.confidence_fill.setGeometry(0, 0, 0, 14)
        self.confidence_fill.setStyleSheet(f"background-color: {MINT}; border: none; border-radius: 6px;")

        chart_panel = QFrame(self)
        chart_panel.setGeometry(930, 380, 410, 208)
        chart_panel.setStyleSheet(f"background-color: {PANEL}; border: 2px solid #b99169; border-radius: 8px;")
        label(chart_panel, "情绪趋势（今日）", (20, 8, 250, 34), 15, 900)
        self.chart = TrendChart(chart_panel)
        self.chart.setGeometry(12, 48, 386, 150)
        tip = QFrame(self)
        tip.setGeometry(302, 632, 642, 94)
        tip.setStyleSheet(f"background-color: {PANEL}; border: 2px solid #d5b58c; border-radius: 7px;")
        tip_icon = QLabel("💡", tip)
        tip_icon.setGeometry(22, 13, 18, 18)
        tip_icon.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        tip_icon.setStyleSheet(
            f"color: {INK}; border: none; font-family: 'Microsoft YaHei'; font-size: 12pt; font-weight: 900;"
        )

        tip_line1 = QLabel("提示：此页面为实时可见预览，方便观察当前情绪状态；", tip)
        tip_line1.setGeometry(42, 10, 580, 24)
        tip_line1.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        tip_line1.setStyleSheet(
            f"color: {INK}; border: none; font-family: 'Microsoft YaHei'; font-size: 10pt; font-weight: 900;"
        )

        tip_line2 = QLabel("即使关闭此页面，后台静默检测仍将持续运行，不会影响数据记录与分析。", tip)
        tip_line2.setGeometry(42, 41, 584, 24)
        tip_line2.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        tip_line2.setStyleSheet(
            f"color: {INK}; border: none; font-family: 'Microsoft YaHei'; font-size: 10pt; font-weight: 900;"
        )

        pet_note = QLabel("我会默默陪伴你，\n记录每一种情绪！", self)
        pet_note.setGeometry(966, 620, 204, 82)
        pet_note.setWordWrap(True)
        pet_note.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        pet_note.setStyleSheet(
            f"background-color: {PANEL}; color: {INK}; border: 2px solid #b99169;"
            "font-family: 'Microsoft YaHei'; font-size: 10pt; font-weight: 900; padding: 8px;"
        )
        mascot = QLabel(self)
        mascot.setGeometry(1188, 614, 120, 120)
        mascot_movie = QMovie(str(self.base_dir / "pet" / "init" / "stay.gif"))
        mascot_movie.setScaledSize(QSize(116, 116))
        mascot.setMovie(mascot_movie)
        mascot_movie.start()
        self.mascot_movie = mascot_movie

    def _open_sidebar_target(self, event, module_id: str) -> None:
        if event.button() == Qt.LeftButton:
            self.open_target(module_id)
            event.accept()

    def _ensure_open(self) -> None:
        if not self.is_enabled():
            self.toggle_recognition()
        self.preview.start_preview(self.camera_select.currentIndex())
        self.refresh()

    def _ensure_closed(self) -> None:
        self.preview.stop_preview()
        if self.is_enabled():
            self.toggle_recognition()
        self.refresh()

    def refresh(self) -> None:
        state = self.get_state()
        enabled = self.is_enabled()
        rows = build_monitor_rows(state, enabled)
        for label_widget, row in zip(self.row_labels, rows):
            label_widget.setText(f"{row.icon}   {row.title}：   {row.value}")
        percent = confidence_percent(state) if enabled else 0
        self.confidence_fill.setFixedWidth(max(0, min(192, int(192 * percent / 100))))
        self.preview.set_state(state, enabled)
        if enabled and not self.preview.active:
            self.preview.start_preview(self.camera_select.currentIndex())
        elif not enabled and self.preview.active:
            self.preview.stop_preview()
        self.chart.set_points(build_trend_points(state, enabled))

