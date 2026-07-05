import unittest
from pathlib import Path

import numpy as np

from moodpet.emotion_camera import (
    OPENVINO_MODEL_BIN_URL,
    OPENVINO_MODEL_XML_URL,
    default_openvino_model_path,
    face_to_blob,
    output_to_scores,
)


class EmotionCameraTest(unittest.TestCase):
    def test_output_to_scores_returns_openvino_emotion_labels(self):
        scores = output_to_scores(np.array([[[[0.1]], [[0.2]], [[0.3]], [[0.4]], [[0.5]]]], dtype="float32"))

        self.assertIn("neutral", scores)
        self.assertIn("anger", scores)
        self.assertEqual(scores["anger"], 0.5)
        self.assertGreater(scores["anger"], scores["neutral"])

    def test_face_to_blob_uses_bgr_openvino_input_shape(self):
        face = np.full((64, 64, 3), 255, dtype=np.uint8)

        blob = face_to_blob(face)

        self.assertEqual(blob.shape, (1, 3, 64, 64))
        self.assertAlmostEqual(float(blob.max()), 255.0, places=5)
        self.assertAlmostEqual(float(blob.min()), 255.0, places=5)

    def test_default_openvino_model_path_replaces_legacy_onnx_name(self):
        model_path = default_openvino_model_path(Path("models") / "emotion-ferplus-8.onnx")

        self.assertEqual(model_path, Path("models") / "emotions-recognition-retail-0003.xml")
        self.assertTrue(OPENVINO_MODEL_XML_URL.endswith(".xml"))
        self.assertTrue(OPENVINO_MODEL_BIN_URL.endswith(".bin"))


if __name__ == "__main__":
    unittest.main()
