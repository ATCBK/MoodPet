import tempfile
import unittest
import urllib.error
from pathlib import Path

from moodpet.mini_game_state import build_choice_image_prompt, build_default_game
from moodpet.seedream_image import SeedreamImageClient, SeedreamImageService, load_seedream_config, post_json


class SeedreamImageTest(unittest.TestCase):
    def test_choice_prompt_keeps_moodpet_pixel_game_style(self):
        state = build_default_game()
        prompt = build_choice_image_prompt(state, state.choices[0])

        self.assertIn("pixel art", prompt)
        self.assertIn("cozy game item illustration", prompt)
        self.assertIn(state.story_title, prompt)
        self.assertIn(state.choices[0].title, prompt)
        self.assertIn("MoodPet", prompt)

    def test_client_posts_seedream_image_generation_request(self):
        captured = {}

        def fake_post(url, payload, headers, timeout):
            captured["url"] = url
            captured["payload"] = payload
            captured["headers"] = headers
            captured["timeout"] = timeout
            return {"data": [{"url": "https://example.test/generated.png"}]}

        client = SeedreamImageClient(
            api_key="ark-secret",
            base_url="https://ark.cn-beijing.volces.com/api/v3",
            model="doubao-seedream-5-0-260128",
            post_json=fake_post,
        )

        self.assertEqual(client.generate_image_url("pixel scene"), "https://example.test/generated.png")
        self.assertEqual(captured["url"], "https://ark.cn-beijing.volces.com/api/v3/images/generations")
        self.assertEqual(captured["headers"]["Authorization"], "Bearer ark-secret")
        self.assertEqual(captured["payload"]["model"], "doubao-seedream-5-0-260128")
        self.assertEqual(captured["payload"]["prompt"], "pixel scene")
        self.assertEqual(captured["payload"]["response_format"], "url")
        self.assertEqual(captured["payload"]["size"], "2K")
        self.assertFalse(captured["payload"]["watermark"])

    def test_service_downloads_and_caches_choice_image(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            download_calls = []

            class FakeClient:
                def generate_image_url(self, prompt):
                    return "https://example.test/generated.png"

                def download_image(self, url):
                    download_calls.append(url)
                    return b"fake-png"

            service = SeedreamImageService(FakeClient(), Path(temp_dir))
            state = build_default_game()

            first_path = service.ensure_choice_image(state, state.choices[0])
            second_path = service.ensure_choice_image(state, state.choices[0])

            self.assertEqual(first_path, second_path)
            self.assertEqual(download_calls, ["https://example.test/generated.png"])
            self.assertTrue(first_path.exists())
            self.assertEqual(first_path.read_bytes(), b"fake-png")
            self.assertIn(state.choices[0].id, first_path.name)

    def test_config_loader_builds_service_only_when_key_exists(self):
        config = load_seedream_config(
            {
                "ARK_API_KEY": "ark-secret",
                "ARK_BASE_URL": "https://ark.cn-beijing.volces.com/api/v3",
                "SEEDREAM_MODEL_ID": "doubao-seedream-5-0-260128",
            }
        )

        self.assertEqual(config.api_key, "ark-secret")
        self.assertEqual(config.endpoint, "https://ark.cn-beijing.volces.com/api/v3/images/generations")

    def test_post_json_includes_http_error_body_for_diagnostics(self):
        class FakeHTTPError(urllib.error.HTTPError):
            def read(self):
                return b'{"error":{"code":"ModelNotOpen","message":"not activated"}}'

        def fake_urlopen(request, timeout):
            raise FakeHTTPError(request.full_url, 404, "Not Found", {}, None)

        import moodpet.seedream_image as seedream_image

        original_urlopen = seedream_image.urllib.request.urlopen
        seedream_image.urllib.request.urlopen = fake_urlopen
        try:
            with self.assertRaisesRegex(RuntimeError, "ModelNotOpen"):
                post_json("https://example.test/images/generations", {}, {}, 1)
        finally:
            seedream_image.urllib.request.urlopen = original_urlopen


if __name__ == "__main__":
    unittest.main()
