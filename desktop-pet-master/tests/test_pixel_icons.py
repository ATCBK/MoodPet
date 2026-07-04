from moodpet.pixel_icons import ICON_ASSETS_DIR, MOODPET_ICONS, icon_asset_path, pixel_icon_name


def test_first_version_icons_use_pixelarticons_only():
    forbidden = {"clipboard", "copy", "paste"}
    allowed_namespaces = {"pixelarticons", "moodpet"}

    assert MOODPET_ICONS
    for feature, icon_name in MOODPET_ICONS.items():
        namespace, icon_id = icon_name.split(":", 1)
        assert namespace in allowed_namespaces
        assert not any(word in feature.lower() for word in forbidden)


def test_recommended_feature_icon_names_are_stable():
    assert pixel_icon_name("realtime") == "pixelarticons:camera"
    assert pixel_icon_name("todo") == "pixelarticons:checklist"
    assert pixel_icon_name("games") == "pixelarticons:gamepad"
    assert pixel_icon_name("settings") == "pixelarticons:sliders"
    assert pixel_icon_name("bubble") == "pixelarticons:message"
    assert pixel_icon_name("message") == "pixelarticons:message"
    assert pixel_icon_name("heart") == "pixelarticons:heart"
    assert pixel_icon_name("calendar") == "pixelarticons:calendar"
    assert pixel_icon_name("sidebar_default") == "moodpet:cat-face"
    assert pixel_icon_name("sidebar_realtime") == "moodpet:realtime-scan"
    assert pixel_icon_name("sidebar_todo") == "moodpet:todo-clipboard"
    assert pixel_icon_name("sidebar_games") == "moodpet:gamepad"
    assert pixel_icon_name("sidebar_settings") == "moodpet:gear"
    assert pixel_icon_name("sidebar_paw") == "moodpet:paw"
    assert pixel_icon_name("close") == "pixelarticons:close"


def test_icon_assets_are_bundled_locally():
    assert ICON_ASSETS_DIR.name == "pixelarticons"
    for feature in MOODPET_ICONS:
        path = icon_asset_path(feature)
        assert path.exists(), f"Missing local icon asset for {feature}: {path}"
        assert path.suffix == ".svg"
