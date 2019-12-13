#
# Copyright 2019 Lars Pastewka
#           2019 Antoine Sanner
#           2019 Kai Haase
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

import os

# Old-style readers
from PyCo.Topography.IO.FromFile import X3PReader, XYZReader, OPDReader, AscReader

# New-style readers
from PyCo.Topography.IO.DI import DIReader
from PyCo.Topography.IO.H5 import H5Reader
from PyCo.Topography.IO.Matlab import MatReader
from PyCo.Topography.IO.MI import MIReader
from PyCo.Topography.IO.NC import NCReader
from PyCo.Topography.IO.NPY import NPYReader
from PyCo.Topography.IO.OPDx import OPDxReader
from PyCo.Topography.IO.IBW import IBWReader


from .Reader import UnknownFileFormatGiven, CannotDetectFileFormat, \
    FileFormatMismatch, CorruptFile, ReaderBase

readers = {
    'asc': AscReader,
    'di': DIReader,
    'mat': MatReader,
    'opd': OPDReader,
    'opdx': OPDxReader,
    'x3p': X3PReader,
    'xyz': XYZReader,
    'ibw': IBWReader,
    'mi': MIReader,
    'nc': NCReader, # NCReader must come before H5Reader, because NC4 *is* HDF5
    'h5': H5Reader,
    'npy': NPYReader,
}


def detect_format(fobj, comm=None):
    """
    Detect file format based on its content.

    Arguments
    ---------
    fobj : filename or file object
    comm : mpi communicator, optional
    """
    msg = ""
    for name, reader in readers.items():
        try:
            if comm is not None:
                reader(fobj, comm)
            else:
                reader(fobj)
            return name
        except Exception as err:
            msg += "tried {}: \n {}\n\n".format(reader.__name__, err)
        finally:
            if hasattr(fobj, 'seek'):
                # if the reader crashes the cursor in the file-like object
                # has to be set back to the top of the file
                fobj.seek(0)
    raise CannotDetectFileFormat(msg)


def open_topography(fobj, format=None, communicator=None):
    r"""
    Returns a reader object for the file `fobj`. The reader interface mirrors
    the topography interface and can be used to extract meta data (number of
    grid points, physical sizes, etc.) without reading the full topography in
    memory.

    Parameters
    ----------
    fobj : str or filelike object
        path of the file or filelike object
    format : str, optional
        specify in which format the file should be interpreted
    communicator : mpi4py or NuMPI communicator object
        MPI communicator handling inter-process communication

    Returns
    -------
    Instance of a `ReaderBase` subclass according to the format.

    Examples
    --------
    Simplest read workflow:

    >>> reader = open_topography("filename")
    >>> top = reader.topography()

    The first topography in file is returned, independently of whether
    the file has multiple channels or not.

    You can always check the channels and their metadata with
    `reader.channels()`. This returns a list of dicts containing attributes `name`,
    `physical_sizes`, `nb_grid_pts`, ``unit` and `height_scale_factor:

    >>> reader.channels
    [{'name': 'ZSensor',
      'nb_grid_pts': (256, 256),
      'physical_sizes': (9999.999999999998, 9999.999999999998),
      'unit': 'nm',
      'height_scale_factor': 0.29638271279074097},
     {'name': 'AmplitudeError',
      'nb_grid_pts': (256, 256),
      'physical_sizes': (10.0, 10.0),
      'unit': ('µm', None),
      'height_scale_factor': 0.04577566528320313}]

    Here the channel 'ZSensor' offers a topography with sizes of
    10000 nm in each dimension.

    You can choose it by giving the index 0 to channel
    (you would use `channel=1` for the second):

    >>> top = reader.topography(channel=0)

    The returned topography has the physical sizes found in the file.

    You can also prescribe some attributes when reading the topography:

    >>> top = reader.topography(channel=0, physical_sizes=(10.,10.), info={"unit":"µm"})
    """
    if communicator is not None:
        kwargs = {"communicator": communicator}
    else:
        kwargs = {}

    if not hasattr(fobj, 'read'):  # fobj is a path
        if not os.path.isfile(fobj):
            raise FileExistsError("file {} not found".format(fobj))

    if format is None:
        msg = ""
        for name, reader in readers.items():
            try:
                return reader(fobj, **kwargs)
            except Exception as err:
                msg += "tried {}: \n {}\n\n".format(reader.__name__, err)
            finally:
                if hasattr(fobj, 'seek'):
                    # if the reader crashes the cursor in the file-like object
                    # has to be set back to the top of the file
                    fobj.seek(0)
        raise CannotDetectFileFormat(msg)
    else:
        if format not in readers.keys():
            raise UnknownFileFormatGiven("{} not in registered file formats {}".format(fobj, readers.keys()))
        return readers[format](fobj, **kwargs)


def read_topography(fn, format=None, communicator=None, **kwargs):
    r"""
    Returns a reader object for the file `fobj`. The reader interface mirrors
    the topography interface and can be used to extract meta data (number of
    grid points, physical sizes, etc.) without reading the full topography in
    memory.

    Parameters
    ----------
    fobj : str or filelike object
        path of the file or filelike object
    format : str, optional
        specify in which format the file should be interpreted
    communicator : mpi4py or NuMPI communicator object
        MPI communicator handling inter-process communication
    channel : int
        Number of the channel to load. See also `channels` method.
    physical_sizes : tuple of floats
        Physical size of the topography. It is necessary to specify this
        if no physical size is found in the data file. If there is a
        physical size, then this parameter will override the physical
        size found in the data file.
    height_scale_factor : float
        Override height scale factor found in the data file.
    info : dict
        This dictionary will be appended to the info dictionary returned
        by the reader.
    periodic: bool
        Wether the Topography should be interpreted as one period of a
        periodic surface. This will affect the PSD and autocorrelation
        calculations (windowing)
    subdomain_locations : tuple of ints
        Origin (location) of the subdomain handled by the present MPI process.
    nb_subdomain_grid_pts : tuple of ints
        Number of grid points within the subdomain handled by the present
        MPI process.

    Returns
    -------
    topography : subclass of :obj:`HeightContainer`
        The object containing the actual topography data.
    """
    with open_topography(fn, format=format, communicator=communicator) as reader:
        t = reader.topography(**kwargs)
    return t
