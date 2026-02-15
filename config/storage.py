from whitenoise.storage import CompressedManifestStaticFilesStorage


class StaticStorage(CompressedManifestStaticFilesStorage):
    """Skip errors for missing source-map files referenced in third-party CSS."""
    manifest_strict = False

    def post_process(self, *args, **kwargs):
        for name, hashed_name, processed in super().post_process(*args, **kwargs):
            if isinstance(processed, Exception):
                # Silently skip missing source-map references (e.g. jazzmin/bootswatch)
                yield name, hashed_name, True
            else:
                yield name, hashed_name, processed
