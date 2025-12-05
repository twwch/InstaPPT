try:
    from ._version import version as __version__
except ImportError:
    try:
        from importlib.metadata import version
        __version__ = version("instappt")
    except ImportError:
        __version__ = "unknown"
