import os, re, errno, subprocess

__version__ = 0.1
__all__ = ['__version__', 'Less']

__LESS_MISSING__ = "`lessc` could not found on the system path.  Please \
ensure that you've properly installed the LESS compiler (http://lesscss.org/)."

def _executable(less):
    def is_exe(fpath):
        return os.path.exists(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(less)
    if fpath:
        if is_exe(less):
            return True
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            exe_file = os.path.join(path, less)
            if is_exe(exe_file):
                return True

    return False


class Less(object):

    def __init__(self, source_path, destination_path, compress=True,
            extension='css', less_path=''):
        """
        Used to automatically parse .less files through lessc and output CSS.

        * Recursively looks for LESS (.less/lss) files in ``source_path``
        * Saves resulting CSS files to ``destination_path``, using the same
          directory structure as the source.

        If ``compress`` is True, compiled resources will also be minified.

        ``extension`` is the file extension used for outputted files, e.g.,
        by default, ``style.less`` becomes ``style.css``.

        By default, the ``lessc`` executable will be searched for on the system
        path.  Optionally, ``less_path`` can be used to specify an absolute
        path to the ``lessc`` executable, e.g., "/some/path/to/less"

        Usage:
        Less('/path/to/less/files', '/path/to/compiled').compile()
        """
        self.source_path = os.path.abspath(source_path)
        self.destination_path = os.path.abspath(destination_path)
        self.compress = compress
        self.extension = extension
        self.lessc = os.path.join(less_path, 'lessc')

    def compile(self, files=None):
        """
        Used to compile a collection of relative (or absolute) filenames.

        When ``files`` is None or empty, ``source_path`` will be recursively
        walked and searched for .less, .lss, and .css files to compile.

        Returns a list of absolute pathnames of written files.
        """
        written = []
        if files is None:
            files = self.__allfiles__
        if isinstance(files, list):
            for f in files:
                written.append(self.__compile_one__(
                    os.path.join(self.source_path, f),
                    self.__to_css__(os.path.join(self.destination_path, f))
                ))
        return filter(None, written)

    def __compile_one__(self, source, destination):
        if self.__mtime__(destination) >= self.__mtime__(source):
            pass # nothing changed!
        else:

            if os.path.splitext(source)[1] == '.css':
                print 'Copying %s to %s' % (source, destination)
                out = open(source, 'r').read()
            else:

                #
                # First, attempt to call lessc without arguments (to ensure
                # that it exists and is executable on the path somewhere)
                #
                if not _executable(self.lessc):
                    raise RuntimeError, __LESS_MISSING__

                print 'Compiling %s to %s' % (source, destination)
                args = [self.lessc, source]
                if self.compress:
                    args.append('-x')

                p = subprocess.Popen(args, stdout=subprocess.PIPE)
                out, err = p.communicate()

            try:
                os.makedirs(os.path.dirname(destination))
            except OSError, e:
                if e.errno != errno.EEXIST: #pragma: no cover
                    raise

            open(destination, 'w').write(out)
            return destination

    def __mtime__(self, filename):
        if not os.path.isfile(filename): return 0
        return os.stat(filename).st_mtime

    def __to_css__(self, filename):
        return re.sub('(le?)ss$', self.extension, filename, re.I)

    @property
    def __allfiles__(self):
        print 'Searching for uncompiled LESS files...'
        matches = []
        for root, dirnames, filenames in os.walk(self.source_path):
          for filename in [f for f in filenames if f.endswith(('.less', '.lss', '.css'))]:
              matches.append(
                os.path.join(root, filename).replace(self.source_path+'/', '', 1)
              )
        return matches
