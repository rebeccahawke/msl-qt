"""
Custom `Qt <https://wiki.python.org/moin/PyQt>`_ components for the UI.
"""
import sys
from collections import namedtuple

from PyQt5 import QtWidgets

__author__ = 'Joseph Borbely'
__copyright__ = '\xa9 2017, ' + __author__
__version__ = '0.1.0'

version_info = namedtuple('version_info', 'major minor micro')(*map(int, __version__.split('.')[:3]))
""":obj:`~collections.namedtuple`: Contains the version information as a (major, minor, micro) tuple."""


def application(args=None):
    """Returns the QApplication instance (creating one if necessary).

    Parameters
    ----------
    args : :obj:`list` of :obj:`str`
        A list of arguments to initialize the QApplication.
        If :obj:`None` then uses :obj:`sys.argv`.

    Returns
    -------
    :obj:`QtWidgets.QApplication`
        The QApplication instance.
    """
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(sys.argv if args is None else args)
    return app

from .loop_until_abort import LoopUntilAbort
