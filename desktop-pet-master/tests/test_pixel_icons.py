from moodpet.pixel_icons import ICON_ASSETS_DIR, MOODPET_ICONS, icon_asset_path, pixel_icon_name


def test_first_version_icons_use_pixelarticons_only():
    forbidden = {"clipboard", "copy", "paste"}

    assert MOODPET_ICONS
    for feature, icon_name in MOODPET_ICONS.items():
        assert icon_name.startswith("pixelarticons:")
        assert not any(word in feature.lower() for word in forbidden)
        assert not any(word in icon_name.lower() for word in forbidden)


def test_recommended_feature_icon_names_are_stable():
    assert pixel_icon_name("realtime") == "pixelarticons:camera"
    assert pixel_icon_name("todo") == "pixelarticons:checklist"
    assert pixel_icon_name("games") == "pixelarticons:gamepad"
    assert pixel_icon_name("settings") == "pixelarticons:sliders"
    assert pixel_icon_name("bubble") == "pixelarticons:message"
    assert pixel_icon_name("close") == "pixelarticons:close"


def test_icon_assets_are_bundled_locally():
    assert ICON_ASSETS_DIR.name == "pixelarticons"
    for feature in MOODPET_ICONS:
        path = icon_asset_path(feature)
        assert path.exists(), f"Missing local icon asset for {feature}: {path}"
        assert path.suffix == ".svg"
