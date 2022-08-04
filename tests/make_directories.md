### Directory Structures

The function `make_directories(structure, at=Path('.'))` is a function to
create dummy directory structures for testing. A directory structure is simply
a hierarchy of directories and files.

A file is represented by a string holding the name of the file. Multiple files
are represented by a list of strings.

A directory is represented by a two-tuple.
The first element contains the name of the directory, while the second element
can be a string representing a single file, or a list of strings representing a
list of files. The second element can also be a list containing more
two-tuples, to represent a nested directory structure.

By default, this directory structure will be created inside the current
directory. To customize the location of this directory structure, supply a
`pathlib.Path` object holding the new location to the `at` argument.

Here are some examples.


**Single file**
```
>>> make_directories('foo.py')
```
A file `foo.py` will be created in the current directory.


**Multiple files**
```
>>> make_directories(['foo.py', 'bar.py'])
```
This will create two files `foo.py` and `bar.py` in the current directory.


**Directory with files**
```
>>> make_directories(
	('foo', ['__init__.py', 'foo.py'])
    )
```
This will create a `foo` directory like this:
```
foo
├──  __init__.py
└── foo.py
```


**Multiple directories**
```
>>> make_directories([
        ('foo', ['__init__.py', 'foo.py']),
        ('bar', ['__init__.py', '__main__.py', 'bar.py']),
    ])
```
The result of this will be two directories `foo` and `bar`:
```
bar
├── bar.py
├── __init__.py
└── __main__.py

foo
├── foo.py
└── __init__.py
```


**Directory with a single file**
```
>>> make_directories(('foo', '__init__.py'))
```
This will create a directory `foo` with a single file `__init__.py`.


**Nested directories**
```
>>> make_directories(
        ('foo', [
            ('bar', ['__init__.py', 'bar.py']),
            ('baz', ['__init__.py', 'baz.py']),
        ]),
    )
```
The result of this will be a directory `foo` with the following structure:
```
foo
├── bar
│   ├── bar.py
│   └── __init__.py
└── baz
    ├── baz.py
    └── __init__.py
```


**Nested directories and files**
```
>>> make_directories([
        ('foo', [
            ('bar', ['__init__.py', 'bar.py']),
            'foo.py',
        ]),
        '__main__.py',
    ])
```
The result of this will be a directory `foo` and a file `__main__.py` as
follows:
```
foo
├── bar
│   ├── bar.py
│   └── __init__.py
└── foo.py
__main__.py
```
