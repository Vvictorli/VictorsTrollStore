import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/update_source.py"
SPEC = importlib.util.spec_from_file_location("update_source", SCRIPT)
update_source = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(update_source)


class UpdateSourceTests(unittest.TestCase):
    def test_build_app_selects_latest_stable_matching_ipa(self):
        releases = [
            {
                "tag_name": "v2.1.2",
                "published_at": "2026-08-24T03:06:40Z",
                "body": "修复 bug",
                "draft": False,
                "prerelease": False,
                "assets": [
                    {
                        "name": "PiliPlus_ios_2.1.2+5241.ipa",
                        "size": 23940004,
                        "browser_download_url": "https://example.test/PiliPlus.ipa",
                    }
                ],
            }
        ]
        config = {
            "name": "PiliPlus",
            "repository": "owner/repo",
            "bundleIdentifier": "com.example.piliplus",
            "developerName": "developer",
            "localizedDescription": "description",
            "iconURL": "https://example.test/icon.png",
            "assetPattern": r"^PiliPlus_ios_.*\.ipa$",
        }

        with patch.object(update_source, "github_releases", return_value=releases):
            app = update_source.build_app(config)

        self.assertEqual("2.1.2", app["version"])
        self.assertEqual("2026-08-24", app["versionDate"])
        self.assertEqual(23940004, app["size"])

    def test_select_release_asset_ignores_prerelease(self):
        releases = [
            {"prerelease": True, "assets": [{"name": "PiliPlus_ios_beta.ipa"}]},
            {"prerelease": False, "draft": False, "assets": [{"name": "PiliPlus_ios_stable.ipa"}]},
        ]

        release, asset = update_source.select_release_asset(releases, r"\.ipa$")

        self.assertFalse(release["prerelease"])
        self.assertEqual("PiliPlus_ios_stable.ipa", asset["name"])

    def test_release_version_supports_prefixed_tag(self):
        version = update_source.release_version(
            "ios16-v1.4.5.1", r"([0-9]+(?:\.[0-9]+)+)$"
        )

        self.assertEqual("1.4.5.1", version)


if __name__ == "__main__":
    unittest.main()
