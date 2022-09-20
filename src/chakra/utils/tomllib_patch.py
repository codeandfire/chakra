try:
    import tomllib
except ModuleNotFoundError:            # tomllib not in standard library for Python < 3.11
    import tomli as tomllib
finally:
    try:
        import tomli_w                 # write support for TOML
    except ModuleNotFoundError:
        pass                           # continue without write support
    else:
        tomllib.dumps = tomli_w.dumps  # augment tomllib with dumps/dump methods
        tomllib.dump = tomli_w.dump

__all__ = ['tomllib']
