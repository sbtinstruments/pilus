from lago.low_level import setup_and_get_assets_dir

_PUBLIC_ASSETS_GIT_URL = "https://github.com/sbtinstruments/assets.git"
_PUBLIC_ASSETS_COMMIT = "7ebc2a5711eaa7c36e5effc265b82cfc10cc64e9"

PUBLIC_ASSETS_DIR = setup_and_get_assets_dir(
    git_url=_PUBLIC_ASSETS_GIT_URL, commit_id=_PUBLIC_ASSETS_COMMIT
)
