"""Some tricks for the `tomllib` module.

The `tomllib` module in the standard library will be available on Python 3.11 and onwards.
Prior versions must install and use the `tomli` package in place of `tomllib`. This code
checks if `tomllib` is available, and otherwise checks for `tomli`.

Another detail is that both `tomllib` and `tomli` provide only read (i.e. parsing)
support, but not write support. For write support, it is recommended to use the `tomli_w`
package, which provides a write API compatible with `tomli`/`tomllib`. This code
monkey-patches the imported `tomllib`/`tomli` module with `dumps()` and `dump()` methods
from `tomli_w` - if `tomli_w` is available - in effect augmenting the module with write
support.
"""


try:
    import tomllib

except ModuleNotFoundError:
    import tomli as tomllib

finally:
    try:
        import tomli_w
    except ModuleNotFoundError:
        # continue without write support.
        pass
    else:
        tomllib.dumps = tomli_w.dumps
        tomllib.dump = tomli_w.dump


__all__ = ['tomllib']
