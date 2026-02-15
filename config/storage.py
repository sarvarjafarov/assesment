from whitenoise.storage import CompressedManifestStaticFilesStorage


class StaticStorage(CompressedManifestStaticFilesStorage):
    """Skip errors for missing source-map files referenced in third-party CSS."""
    manifest_strict = False
