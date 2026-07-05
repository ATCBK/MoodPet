import math
import queue
import shutil
import ssl
import threading
import time
import urllib.request
from pathlib import Path
from typing import Callable, Dict, Iterable, Optional, Tuple

import cv2
import numpy as np

from moodpet.emotion import OPENVINO_EMOTION_LABELS, EmotionState, best_openvino_emotion, build_emotion_state


OPENVINO_MODEL_NAME = "emotions-recognition-retail-0003"
OPENVINO_MODEL_XML_URL = (
    "https://storage.openvinotoolkit.org/repositories/open_model_zoo/2023.0/models_bin/1/"
    "emotions-recognition-retail-0003/FP32/emotions-recognition-retail-0003.xml"
)
OPENVINO_MODEL_BIN_URL = (
    "https://storage.openvinotoolkit.org/repositories/open_model_zoo/2023.0/models_bin/1/"
    "emotions-recognition-retail-0003/FP32/emotions-recognition-retail-0003.bin"
)


def softmax(values: np.ndarray) -> np.ndarray:
    flattened = values.astype("float32").reshape(-1)
    shifted = flattened - np.max(flattened)
    exp_values = np.exp(shifted)
    return exp_values / np.sum(exp_values)


def output_to_scores(output: np.ndarray) -> Dict[str, float]:
    probabilities = output.astype("float32").reshape(-1)
    total = float(np.sum(probabilities))
    if total <= 0 or not math.isfinite(total):
        probabilities = softmax(output)
    usable_count = min(len(OPENVINO_EMOTION_LABELS), len(probabilities))
    return {
        OPENVINO_EMOTION_LABELS[index]: float(probabilities[index])
        for index in range(usable_count)
        if math.isfinite(float(probabilities[index]))
    }


def face_to_blob(face: np.ndarray) -> np.ndarray:
    face = cv2.resize(face, (64, 64))
    return cv2.dnn.blobFromImage(
        face,
        scalefactor=1.0,
        size=(64, 64),
        mean=(0, 0, 0),
        swapRB=False,
    )


def default_openvino_model_path(model_path: Path) -> Path:
    if model_path.suffix.lower() == ".xml":
        return model_path
    return model_path.parent / f"{OPENVINO_MODEL_NAME}.xml"


def open_camera_capture(
    camera_index: int = 0,
    capture_factory: Callable[[int, int], cv2.VideoCapture] = cv2.VideoCapture,
    fallback_indices: Iterable[int] = (0, 1),
) -> Tuple[Optional[cv2.VideoCapture], Optional[int]]:
    candidate_indices = []
    for index in (camera_index, *fallback_indices):
        if index not in candidate_indices:
            candidate_indices.append(index)

    for index in candidate_indices:
        for backend in (cv2.CAP_DSHOW, cv2.CAP_ANY):
            camera = capture_factory(index, backend)
            if camera.isOpened():
                return camera, index
            camera.release()
    return None, None


def download_model_file(url: str, target_path: Path) -> None:
    try:
        urllib.request.urlretrieve(url, target_path)
        return
    except Exception:
        pass

    context = ssl._create_unverified_context()
    with urllib.request.urlopen(url, context=context) as response, target_path.open("wb") as target:
        shutil.copyfileobj(response, target)


def ensure_model(model_path: Path) -> None:
    model_path = default_openvino_model_path(model_path)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    bin_path = model_path.with_suffix(".bin")
    if not model_path.exists() or model_path.stat().st_size == 0:
        download_model_file(OPENVINO_MODEL_XML_URL, model_path)
    if not bin_path.exists() or bin_path.stat().st_size == 0:
        download_model_file(OPENVINO_MODEL_BIN_URL, bin_path)


class OpenVINOEmotionModel:
    def __init__(self, model_path: Path) -> None:
        try:
            from openvino import Core
        except ModuleNotFoundError as exc:
            raise RuntimeError("未安装 OpenVINO，请先安装 openvino 依赖。") from exc

        core = Core()
        model = core.read_model(str(model_path))
        self.compiled_model = core.compile_model(model, "CPU")
        self.input_layer = self.compiled_model.input(0)
        self.output_layer = self.compiled_model.output(0)

    def predict(self, blob: np.ndarray) -> np.ndarray:
        return self.compiled_model([blob])[self.output_layer]


def load_emotion_model(model_path: Path) -> OpenVINOEmotionModel:
    model_path = default_openvino_model_path(model_path)
    return OpenVINOEmotionModel(model_path)


class EmotionCameraWorker:
    def __init__(
        self,
        output_queue: "queue.Queue[EmotionState]",
        model_path: Path,
        camera_index: int = 0,
        interval_seconds: float = 2.5,
    ) -> None:
        self.output_queue = output_queue
        self.model_path = model_path
        self.camera_index = camera_index
        self.interval_seconds = interval_seconds
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> None:
        if self.running:
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, name="MoodPetEmotionCamera", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)

    def _publish(self, state: EmotionState) -> None:
        try:
            self.output_queue.put_nowait(state)
        except queue.Full:
            try:
                self.output_queue.get_nowait()
            except queue.Empty:
                pass
            self.output_queue.put_nowait(state)

    def _run(self) -> None:
        try:
            ensure_model(self.model_path)
            net = load_emotion_model(self.model_path)
            cascade_path = Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml"
            face_detector = cv2.CascadeClassifier(str(cascade_path))
            if face_detector.empty():
                self._publish(build_emotion_state("error", message="未找到 OpenCV 人脸检测器。"))
                return

            camera, selected_index = open_camera_capture(self.camera_index)
            if camera is not None and selected_index is not None:
                self.camera_index = selected_index
            if camera is None or not camera.isOpened():
                self._publish(build_emotion_state("error", message="无法打开摄像头。"))
                return

            try:
                self._capture_loop(camera, face_detector, net)
            finally:
                camera.release()
        except Exception as exc:
            self._publish(build_emotion_state("error", message=f"情绪识别异常：{exc}"))

    def _capture_loop(
        self,
        camera: cv2.VideoCapture,
        face_detector: cv2.CascadeClassifier,
        net: OpenVINOEmotionModel,
    ) -> None:
        while not self._stop_event.is_set():
            ok, frame = camera.read()
            if not ok or frame is None:
                self._publish(build_emotion_state("error", message="读取摄像头画面失败。"))
                time.sleep(self.interval_seconds)
                continue

            state = self._analyze_frame(frame, face_detector, net)
            self._publish(state)
            time.sleep(self.interval_seconds)

    def _analyze_frame(
        self,
        frame: np.ndarray,
        face_detector: cv2.CascadeClassifier,
        net: OpenVINOEmotionModel,
    ) -> EmotionState:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_detector.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(80, 80),
        )
        if len(faces) == 0:
            return build_emotion_state("away", 0.0, face_detected=False)

        x, y, w, h = max(faces, key=lambda face: face[2] * face[3])
        face = frame[y : y + h, x : x + w]
        blob = face_to_blob(face)
        output = net.predict(blob)
        scores = output_to_scores(output)
        return best_openvino_emotion(scores)
