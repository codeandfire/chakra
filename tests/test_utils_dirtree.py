import json
import shutil
import random
import unittest

from chakra.core import Command
from chakra.utils import HDirectory, HFile
from chakra.utils import tempfile

NO_TREE = False
if Command(['tree', '--version']).run().returncode != 0:
    NO_TREE = True

def _run_tree(dir_):
    out = Command(['tree', dir_, '-J']).run().stdout
    tree = json.loads(out)

    assert tree[-1]['type'] == 'report'   # separate out report
    report = tree.pop(-1)

    assert tree[0]['name'] == dir_        # topmost entry is the directory scanned
    tree = tree[0]['contents']            # we are interested in this directory's contents
    return (tree, report)

class TestNSubdirectories(unittest.TestCase):
    NDIRS = 10

    def setUp(self):
        subdirs = [
            HDirectory(f'subdir{i}', files=[HFile(f'file{i}.txt')])
            for i in range(self.NDIRS)]
        root = HDirectory('root', subdirs=subdirs)
        self.root = root

    @unittest.skipIf(NO_TREE, 'tree is not installed')
    def test_structure(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.root.create(tmp)
            tree, report = _run_tree(tmp)

        assert len(tree) == 1                           # only one directory, the 'root'
        assert tree[0]['name'] == 'root'
        tree = tree[0]['contents']                      # step into root's contents

        assert len(tree) == self.NDIRS                  # subdirectories
        for i, t in enumerate(tree):
            assert t['name'] == f'subdir{i}'
            assert len(t['contents']) == 1              # only one file
            assert t['contents'][0]['name'] == f'file{i}.txt'

        assert report['files'] == self.NDIRS
        assert report['directories'] == self.NDIRS+1    # subdirectories + root

    def test_api(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.root.create(tmp)

            for i in (0, self.NDIRS//2, self.NDIRS-1):  # some selected cases
                with self.subTest(i=i):
                    assert self.root.subdirs[f'subdir{i}'].path.exists()
                    assert self.root.subdirs[f'subdir{i}'].files[f'file{i}.txt'].path.exists()

    def test_load(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.root.create(tmp)

            del self.root; self.setUp()                 # reset all context
            self.root.load(tmp)                    # should happen without errors

            i = self.NDIRS-1                            # selected case
            self.root.subdirs[f'subdir{i}'].files[f'file{i}.txt'].path.unlink()
            del self.root; self.setUp()
            with self.assertRaises(RuntimeError):
                self.root.load(tmp)

class TestBinaryTree(unittest.TestCase):
    LEVEL = 5

    def setUp(self):

        def _setup(l, prior=[]):
            n = 2 ** (l-1)
            if l == self.LEVEL:
                next_ = [HFile(f'file{l}{i}.txt') for i in range(n)]
            elif l == self.LEVEL-1:
                next_ = [
                    HDirectory(f'subdir{l}{i}', files=[prior[2*i], prior[2*i+1]])
                    for i in range(n)]
            else:
                next_ = [
                    HDirectory(f'subdir{l}{i}', subdirs=[prior[2*i], prior[2*i+1]])
                    for i in range(n)]
            if n == 1:
                return next_[0]
            return _setup(l-1, prior=next_)

        self.root = _setup(self.LEVEL)

    @unittest.skipIf(NO_TREE, 'tree is not installed')
    def test_structure(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.root.create(tmp)
            tree, report = _run_tree(tmp)

        # "unpack" the tree, asserting at each "unpacking" that the number of contents
        # unpacked are 2.

        l = 1
        while l < self.LEVEL:
            newtree = []
            l += 1
            for t in tree:
                conts = t['contents']
                assert len(conts) == 2
                if l == self.LEVEL:
                    assert all(c['type'] == 'file' for c in conts)
                else:
                    assert all(c['type'] == 'directory' for c in conts)
                newtree.extend(conts)
            tree = newtree

        assert report['files'] == 2 ** (self.LEVEL - 1)
        assert report['directories'] == 2 ** (self.LEVEL - 1) - 1

    def test_api(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.root.create(tmp)

            # walk a random path down the tree.

            i, chosen = 0, self.root
            for l in range(2, self.LEVEL+1):
                assert chosen.path.exists()
                i1, i2 = 2*i, 2*i+1
                if l == self.LEVEL:
                    assert chosen.files[f'file{l}{i1}.txt'].path.exists()
                    assert chosen.files[f'file{l}{i2}.txt'].path.exists()
                else:
                    assert chosen.subdirs[f'subdir{l}{i1}'].path.exists()
                    assert chosen.subdirs[f'subdir{l}{i2}'].path.exists()
                    i = i2 if random.random() > 0.5 else i1
                    chosen = chosen.subdirs[f'subdir{l}{i}']

    def test_load(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.root.create(tmp)

            del self.root; self.setUp()
            self.root.load(tmp)

            # delete a randomly chosen directory at level (self.LEVEL-2) in the tree.

            i, chosen = 0, self.root
            for l in range(2, self.LEVEL-1):
                i1, i2 = 2*i, 2*i+1
                i = i2 if random.random() > 0.5 else i1
                chosen = chosen.subdirs[f'subdir{l}{i}']
            shutil.rmtree(chosen.path)

            del self.root; self.setUp()
            with self.assertRaises(RuntimeError):
                self.root.load()

class TestFilesOnly(unittest.TestCase):
    NFILES = 10

    def setUp(self):
        self.root = HDirectory(
            'root', files=[HFile(f'file{i}.txt') for i in range(self.NFILES)])

    @unittest.skipIf(NO_TREE, 'test is not installed')
    def test_structure(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.root.create(tmp)
            tree, report = _run_tree(tmp)

        assert len(tree) == 1
        assert tree[0]['name'] == 'root'
        tree = tree[0]['contents']

        assert len(tree) == self.NFILES
        for i, t in enumerate(tree):
            assert t['name'] == f'file{i}.txt'
            assert t['type'] == 'file'

        assert report['files'] == self.NFILES
        assert report['directories'] == 1

    def test_api(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.root.create(tmp)

            assert self.root.path.exists()
            for i in range(self.NFILES):
                assert self.root.files[f'file{i}.txt'].path.exists()
            assert len(self.root.subdirs) == 0

    def test_load(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.root.create(tmp)

            del self.root; self.setUp()
            self.root.load(tmp)

            shutil.rmtree(self.root.path)               # remove everything
            del self.root; self.setUp()
            with self.assertRaises(RuntimeError):
                self.root.load(tmp)

class TestEmptyDirectoriesAndFiles(unittest.TestCase):
    NDIRS = 10
    NFILES = 5

    def setUp(self):
        subdirs = [HDirectory(f'subdir{i}') for i in range(self.NDIRS)]
        files = [HFile(f'file{i}.txt') for i in range(self.NFILES)]
        self.root = HDirectory('root', subdirs=subdirs, files=files)

    @unittest.skipIf(NO_TREE, 'tree is not installed')
    def test_structure(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.root.create(tmp)
            tree, report = _run_tree(tmp)

        assert len(tree) == 1
        assert tree[0]['name'] == 'root'
        tree = tree[0]['contents']

        assert len(tree) == self.NDIRS + self.NFILES
        for t in tree:
            if t['name'].endswith('.txt'):
                assert t['type'] == 'file'
            elif t['name'].startswith('subdir'):
                assert t['type'] == 'directory'

        assert report['files'] == self.NFILES
        assert report['directories'] == self.NDIRS + 1

    def test_api(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.root.create(tmp)

            for i in range(self.NFILES):
                assert self.root.files[f'file{i}.txt'].path.exists()
            for i in range(self.NDIRS):
                assert self.root.subdirs[f'subdir{i}'].path.exists()
                assert len(self.root.subdirs[f'subdir{i}'].subdirs) == 0
                assert len(self.root.subdirs[f'subdir{i}'].files) == 0

    def test_load(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.root.create(tmp)

            del self.root; self.setUp()
            self.root.load(tmp)

            # delete a randomly chosen directory.

            i = random.choice(range(0, self.NDIRS))
            self.root.subdirs[f'subdir{i}'].path.rmdir()
            del self.root; self.setUp()
            with self.assertRaises(RuntimeError):
                self.root.load(tmp)
