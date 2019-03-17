#
# Copyright 2019 k.o.haase@googlemail.com
#           2018-2019 Antoine Sanner
# 
# ### MIT license
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
"""

In MPI Parallelized programs:

- we have to use `MPI.File.Open` instead of `open` to allow several processors to access the same file simultaneously
- make the file reading in 3 steps:
    - read the resolution only
    - make the domain decomposition according to the resolution
    - load the relevant subdomain on each processor

TODO: We should implement the interpretation of the headers and the metadata at
      the same place for serialized and parallelized code, but the loading in
      serialized code should not rely on the mpi4py library (MPI.File.open())
      MPI.File.open() uses buffers and does not have exactly the same interface
      as open()
      Maybe we can do some wrapper that provides equivalent interface ?
"""


try: #TODO: Code should look like the same with and without mpi4py
    from mpi4py import MPI
    _with_mpi = True
except:
    _with_mpi = False
if _with_mpi:
    import MPITools.FileIO #TODO: MPITools should provide the same interface with and without mpi4py

from PyCo.Topography import Topography

import abc
from numpy.lib.format import read_magic, _read_array_header, _check_version
import numpy as np

# TODO: langfristig sollten alle ladefunktionen nur einmal implementiert werden, sowohl MPI und seriell-fähig

class ReadFileError(Exception):
    pass


class UnknownFileFormatGiven(ReadFileError):
    pass

class CannotDetectFileFormat(ReadFileError):
    """
    Raised when no reader is able to read the file
    """

class FileFormatMismatch(ReadFileError):
    """
    Raised when the reader cannot interpret the file at all
    (obvious for txt vs binary, but holds also for a header)
    """
    pass

class CorruptFile(ReadFileError):
    """
    Raised when the reader identifies the file format as matching, but there is a mistake, for example the number of points doesn't match
    """
    pass

# TODO: This piece of code is mpi dependent
class MPITopographyLoader():
    def __init__(self, fn, comm, format = None):
        """

        Parameters
        ----------
        fn
        comm
        format
        """
        self.size = None  # will stay None if the file doesn't provide the information.
        self.unit = None
        self._info={}

        #TODO: I'm not shure that it makes sense to implement generic readers
        # for all data types.
        self.mpi_file = MPITools.FileIO.make_mpi_file_view(fn, comm, format=format)
        self.dtype = self.mpi_file.dtype
        self.resolution = self.mpi_file.resolution

        # TODO: maybe implement extras specific to Topography , like loading the units and the size

    def topography(self, substrate):
        """
        Returns the `Topography` object containing the data attributed to the
        processors. `substrate` prescribes the domain decomposition.
        Parameters
        ----------
        substrate: Free- or PeriodicFFTElasticHalfspace instance
        has attributes topography_subdomain_location, topography_subdomain_resolution and resolution
        Returns
        -------
        Topography
        """
        # TODO: Are sometimes the Units Stored?
        return Topography(
            heights=self.mpi_file.read(subdomain_location=substrate.topography_subdomain_location,
                                       subdomain_resolution=substrate.topography_subdomain_resolution),
            subdomain_location=substrate.topography_subdomain_location,
            resolution=substrate.resolution,
            pnp=substrate.pnp,
            size=self.size  )

class TopographyLoader(metaclass=abc.ABCMeta):
    def __init__(self, size=None,  info=None):
        """
        reads the metadata out of the file
        """
        self.size = size  # will stay None if the file doesn't provide the information.
        self.info = info

    @abc.abstractmethod
    def topography(self):
        """
        returns a `Topography` instance containing the data

        Returns
        -------
        """
        raise NotImplementedError


class TopographyLoaderH5(TopographyLoader):
    def __init__(self, fobj, size=None, info=None):
        super().__init__(size, info)

        # TODO: extract size etc. from the file ? If size provided as argument,
        #  check if it's the same then provided by the file ?
        import h5py
        self._h5 = h5py.File(fobj)

    def topography(self):
        return Topography(self._h5['surface'][...], size= self.size)


class TopographyLoaderNPY:
    """
    npy is a fileformat made specially for numpy arrays. They contain no extra
    metadata so we use straightforwardly the implementation from numpy and MPITools
    """
    def __init__(self, fn, comm=None):
        """

        Parameters
        ----------
        fn: filename
        comm: MPI communicator
        """
        self.size = None  # will stay None if the file doesn't provide the information.
        self.info={}

        if _with_mpi: # TODO: not ok code should look the same for MPI and nonmpi: have to write stub for MPI.File
            if comm is None:
                raise ValueError("you should provide comm when running with MPI")
            self.mpi_file = MPITools.FileIO.make_mpi_file_view(fn, comm, format=format)
            self.dtype = self.mpi_file.dtype
            self.resolution = self.mpi_file.resolution
        else: # just use the functions from numpy
            self.file=open(fn, "rb")
            try:
                version = read_magic(self.file)
                _check_version(version)
                self.resolution, fortran_order, self.dtype = _read_array_header(self.file, version)
            except ValueError:
                raise CannotDetectFileFormat()

        # TODO: maybe implement extras specific to Topography , like loading the units and the size

    def topography(self, substrate=None):
        """
        Returns the `Topography` object containing the data attributed to the
        processors. `substrate` prescribes the domain decomposition.
        Parameters
        ----------
        substrate: Free- or PeriodicFFTElasticHalfspace instance
        has attributes topography_subdomain_location, topography_subdomain_resolution and resolution
        Returns
        -------
        Topography
        """
        # TODO: Are sometimes the Units Stored?
        if _with_mpi:
            if ( substrate is None ):
                raise ValueError("you should provide substrate to specify the domain decomposition")

            return Topography(
                heights=self.mpi_file.read(subdomain_location=substrate.topography_subdomain_location,
                                           subdomain_resolution=substrate.topography_subdomain_resolution),
                subdomain_location=substrate.topography_subdomain_location,
                resolution=substrate.resolution,
                pnp=substrate.pnp,
                size=self.size,
                info =self.info)

        else:
            array = np.fromfile(self.file, dtype=self.dtype,
                    count=np.multiply.reduce(self.resolution, dtype=np.int64))
            array.shape = self.resolution
            self.file.close() # TODO: Or make this in the destructor ?
            return Topography(heights=array, size=self.size)

readers = {
        "npy": TopographyLoaderNPY,
        "h5": TopographyLoaderH5,
    }

def detect_format(fn, comm=None):
    """
    Detect file format based on its content.

    Keyword Arguments:
    fobj : filename or file object
    comm : mpi communicator, optional
    """

    for name, reader in readers.items():
        try:
            if comm is not None:
                reader(fn, comm)
            else:
                reader(fn)
            return name
        except :
            CannotDetectFileFormat()

def read(fn, format=None, comm=None):
    """

    Parameters
    ----------
    fn
    format
    comm

    Returns
    -------

    """
    if comm is not None:
        kwargs = {"comm":comm}
    else: kwargs= {}

    if format is None:
        for name, reader in readers.items():
            try:
                return reader(fn, **kwargs)
            except:
                pass
            raise CannotDetectFileFormat()
    else:
        if format not in readers.keys():
            raise UnknownFileFormatGiven("{} not in registered file formats {}".format(fn, readers.keys()))
        return readers[format](fn, **kwargs)




# TODO: Does this belong here ?
def save_npy(fn, topography):
    MPITools.FileIO.save_npy(fn=fn, data=topography.heights(), subdomain_location=topography.subdomain_location,
                       resolution=topography.subdomain_resolution, comm=topography.comm)
