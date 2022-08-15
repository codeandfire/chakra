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
