from pathlib import Path
import subprocess
import textwrap


class SamplePackage(object):

    def __init__(
            self, name, version='0.1.0', layout='src', dependencies=[],
            build_requires=[], subpackage_name=None,
        ):
        """A sample package.

        Specify the name and optionally the version, layout ('src' or 'flat'),
        dependencies, build-time dependencies, and the name of a subpackage.
        """

        self.name = name
        self.version = version
        self.layout = layout
        self.dependencies = dependencies
        self.build_requires = build_requires
        self.subpackage_name = subpackage_name

    def create(self):
        """Create the package.

        Writes a `pyproject.toml` file and creates a minimal directory structure with the
        package in the required layout, and containing an `__init__.py` and a
        `module.py`. A subpackage is also created (if its name has been specified), again
        with the same two `.py` files.
        """

        if self.layout == 'src':
            package_dir = Path('src') / Path(self.name)
            package_dir.mkdir(parents=True)
        elif self.layout == 'flat':
            package_dir = Path(self.name)
            package_dir.mkdir()
        else:
            raise ValueError("layout must be one of 'src' or 'flat'")

        pyproject_toml = Path('pyproject.toml')
        pyproject_toml.write_text(
            textwrap.dedent(f"""
                [project]
                name = "{self.name}"
                version = "{self.version}"
                dependencies = {self.dependencies}

                [build-system]
                requires = {self.build_requires}

                [tool.chakra.source]
                packages = ["{self.name}"]
            """)
        )

        (package_dir / Path('__init__.py')).touch()
        (package_dir / Path('module.py')).touch()

        if self.subpackage_name is not None:
            subpackage_dir = package_dir / Path(self.subpackage_name)
            subpackage_dir.mkdir()
            (subpackage_dir / Path('__init__.py')).touch()
            (subpackage_dir / Path('module.py')).touch()


def is_installed(dep, env_path, version=None):
    """Check that the dependency `dep` is installed in the environment at `env_path`.

    Optionally specify the version of the dependency that you expect to be installed, in
    order to enable a stricter check.

    This function works by deducing the `site-packages` directory of the given environment
    and checking if, in this `site-packages` directory:
        1. A top-level directory or top-level module with the same name as `dep` exists;
        2. and, a `.dist-info` directory corresponding to `dep` exists.
    """

    site_packages = (env_path / Path('lib'))
    site_packages = list(site_packages.glob('python*'))[0]
    site_packages = site_packages / Path('site-packages')

    if (site_packages / Path(dep)).exists() or \
            (site_packages / Path(f'{dep}.py')).exists():

        if version is None:
            if len(list(site_packages.glob(f'{dep}-*.dist-info'))) == 1:
                return True
        else:
            if (site_packages / Path(f'{dep}-{version}.dist-info')).exists():
                return True

    return False
