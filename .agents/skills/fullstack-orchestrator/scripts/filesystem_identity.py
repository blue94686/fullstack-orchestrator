"""Resolve existing directory spellings without assuming case/Unicode semantics."""
import os
import sys
import stat
from pathlib import Path


def canonical_directory(value):
    path = Path(value).expanduser().resolve(strict=True)
    if not path.is_dir() or path.parent == path:
        raise ValueError('expected an existing non-root directory')
    if sys.platform == 'darwin':
        # F_GETPATH asks the kernel for the vnode path, unifying APFS firmlinks.
        # Verify identity before trusting it; never hardcode volume mappings.
        import fcntl
        fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
        try:
            resolved = Path(os.fsdecode(fcntl.fcntl(fd, 50, bytes(1024)).split(b'\0')[0]))
            info, actual = os.fstat(fd), resolved.stat()
            if (info.st_dev, info.st_ino) != (actual.st_dev, actual.st_ino):
                raise ValueError('directory identity changed; reconcile paths')
            path = resolved
        finally:
            os.close(fd)
    # realpath resolves symlinks, but on macOS may preserve an alias spelling.
    # Read the actual directory entry at each level instead of lowercasing it.
    current = Path(path.anchor)
    for component in path.parts[1:]:
        target = (current / component).stat()
        matches = []
        with os.scandir(current) as entries:
            for entry in entries:
                try:
                    # APFS firmlinks can expose a different readdir inode.
                    info = entry.stat(follow_symlinks=False)
                except FileNotFoundError:
                    continue  # An unrelated sibling may disappear during enumeration.
                if (info.st_dev, info.st_ino) == (target.st_dev, target.st_ino):
                    matches.append(entry.name)
        if len(matches) != 1:
            raise ValueError('directory identity changed or is ambiguous; reconcile paths')
        current = current / matches[0]
    return str(current)


def is_observable_directory(value):
    try:
        return stat.S_ISDIR(Path(value).stat().st_mode)
    except (FileNotFoundError, NotADirectoryError):
        return False


def observed_path(value):
    """Bind legacy path spellings where observable; retain missing old locks."""
    try:
        if is_observable_directory(value):
            return canonical_directory(value)
        raise FileNotFoundError(value)
    except (FileNotFoundError, NotADirectoryError):
        path, suffix = Path(value), []
        # Legacy records may outlive a directory or an ancestor replaced by a
        # regular file. Keep their textual lock under the observable ancestor.
        # Permission errors still propagate instead of weakening exclusion.
        while not is_observable_directory(path) and path.parent != path:
            suffix.insert(0, path.name)
            path = path.parent
        base = str(path) if path.parent == path else canonical_directory(path)
        return str(Path(base).joinpath(*suffix))
