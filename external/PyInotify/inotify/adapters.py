import logging
import select
import os
import struct
import collections
import time

from errno import EINTR
from typing import List

import external.PyInotify.inotify.constants
import external.PyInotify.inotify.calls

# Constants.

_DEFAULT_EPOLL_BLOCK_DURATION_S = 1
_HEADER_STRUCT_FORMAT = 'iIII'

_DEFAULT_TERMINAL_EVENTS = (
    'IN_Q_OVERFLOW',
    'IN_UNMOUNT',
)

# Globals.

_INOTIFY_EVENT = collections.namedtuple(
                    '_INOTIFY_EVENT',
                    [
                        'wd',
                        'mask',
                        'cookie',
                        'len',
                    ])

_STRUCT_HEADER_LENGTH = struct.calcsize(_HEADER_STRUCT_FORMAT)
_IS_DEBUG = bool(int(os.environ.get('DEBUG', '0')))


class EventTimeoutException(Exception):
    pass


class TerminalEventException(Exception):
    def __init__(self, type_name, event):
        super(TerminalEventException, self).__init__(type_name)
        self.event = event


class Inotify(object):
    def __init__(self, logger, paths=[], block_duration_s=_DEFAULT_EPOLL_BLOCK_DURATION_S):
        self.__block_duration = block_duration_s
        self.__watches = {}
        self.__watches_r = {}
        self.__buffer = b''
        self.__logger = logger

        self.__inotify_fd = external.PyInotify.inotify.calls.inotify_init()
        self.__logger.debug("Inotify handle is (%d).", self.__inotify_fd)

        self.__epoll = select.epoll()
        self.__epoll.register(self.__inotify_fd, select.POLLIN)

        self.__last_success_return = None

        for path in paths:
            self.add_watch(path)

    def __get_block_duration(self):
        """Allow the block-duration to be an integer or a function-call."""

        try:
            return self.__block_duration()
        except TypeError:
            # A scalar value describing seconds.
            return self.__block_duration

    def __del__(self):
        self.__logger.debug("Cleaning-up external.PyInotify.inotify.")
        os.close(self.__inotify_fd)

    def _get_watches(self):
        return self.__watches
    
    def get_watch_id(self, path_unicode):
        return self.__watches.get(path_unicode)
        
    def add_watch(self, path_unicode, mask=external.PyInotify.inotify.constants.IN_ALL_EVENTS):
        self.__logger.debug("Adding watch: [%s]", path_unicode)

        # Because there might be race-conditions in the recursive handling (see
        # the notes in the documentation), we recommend to add watches using
        # data from a secondary channel, if possible, which means that we might
        # then be adding it, yet again, if we then receive it in the normal
        # fashion afterward.
        if path_unicode in self.__watches:
            return

        path_bytes = path_unicode.encode('utf8')

        wd = external.PyInotify.inotify.calls.inotify_add_watch(self.__inotify_fd, path_bytes, mask)
        self.__logger.debug("Added watch (%d): [%s]", wd, path_unicode)

        if wd < 0:
            self.__logger.warning('PyInotify - add_watch for path {} returned invalid'.format(wd))
        else:
            self.__watches[path_unicode] = wd
            self.__watches_r[wd] = path_unicode

        return wd

    def remove_watch(self, path, superficial=False):
        """Remove our tracking information and call inotify to stop watching
        the given path. When a directory is removed, we'll just have to remove
        our tracking since inotify already cleans-up the watch.
        """

        wd = self.__watches.get(path)
        if wd is None:
            return

        self.__logger.debug("Removing watch for watch-handle (%d): [%s]",
                      wd, path)

        del self.__watches[path]

        self.remove_watch_with_id(wd, superficial)
    
    def remove_watch_with_id(self, wd, superficial=False):
        del self.__watches_r[wd]

        if superficial is False:
            self.__logger.debug("Removing watch for watch-handle (%d).", wd)

            external.PyInotify.inotify.calls.inotify_rm_watch(self.__inotify_fd, wd)

    def remove_watch_and_sub_watches(self, path):
        watch_found = True
        while watch_found == True:
            watch_found = False
            for watch_path in self.__watches:
                if watch_path.startswith(path) == True:
                    self.remove_watch(watch_path, True)
                    watch_found = True
                    break
    
    def _get_event_names(self, event_type):
        names = []
        for bit, name in external.PyInotify.inotify.constants.MASK_LOOKUP.items():
            if event_type & bit:
                names.append(name)
                event_type -= bit

                if event_type == 0:
                    break

        assert event_type == 0, \
               "We could not resolve all event-types: (%d)" % (event_type,)

        return names

    def _handle_inotify_event(self, wd):
        """Handle a series of events coming-in from external.PyInotify.inotify."""

        b = os.read(wd, 1024)
        if not b:
            return

        self.__buffer += b

        while 1:
            length = len(self.__buffer)

            if length < _STRUCT_HEADER_LENGTH:
                self.__logger.debug("Not enough bytes for a header.")
                return

            # We have, at least, a whole-header in the buffer.

            peek_slice = self.__buffer[:_STRUCT_HEADER_LENGTH]

            header_raw = struct.unpack(
                            _HEADER_STRUCT_FORMAT,
                            peek_slice)

            header = _INOTIFY_EVENT(*header_raw)
            type_names = self._get_event_names(header.mask)
            self.__logger.debug("Events received in stream: {}".format(type_names))

            event_length = (_STRUCT_HEADER_LENGTH + header.len)
            if length < event_length:
                return

            filename = self.__buffer[_STRUCT_HEADER_LENGTH:event_length]

            # Our filename is 16-byte aligned and right-padded with NULs.
            filename_bytes = filename.rstrip(b'\0')

            self.__buffer = self.__buffer[event_length:]

            path = self.__watches_r.get(header.wd)
            if path is not None:
                filename_unicode = filename_bytes.decode('utf8')
                yield (header, type_names, path, filename_unicode)

            buffer_length = len(self.__buffer)
            if buffer_length < _STRUCT_HEADER_LENGTH:
                break

    def event_gen(
            self, timeout_s=None, yield_nones=True, filter_predicate=None,
            terminal_events=_DEFAULT_TERMINAL_EVENTS):
        """Yield one event after another. If `timeout_s` is provided, we'll
        break when no event is received for that many seconds.
        """

        # We will either return due to the optional filter or because of a
        # timeout. The former will always set this. The latter will never set
        # this.
        self.__last_success_return = None

        last_hit_s = time.time()
        while True:
            block_duration_s = self.__get_block_duration()

            # Poll, but manage signal-related errors.

            try:
                events = self.__epoll.poll(block_duration_s)
            except IOError as e:
                if e.errno != EINTR:
                    raise

                if timeout_s is not None:
                    time_since_event_s = time.time() - last_hit_s
                    if time_since_event_s > timeout_s:
                        break

                continue

            # Process events.

            for fd, event_type in events:
                # (fd) looks to always match the inotify FD.

                names = self._get_event_names(event_type)
                self.__logger.debug("Events received from epoll: {}".format(names))

                for (header, type_names, path, filename) \
                        in self._handle_inotify_event(fd):
                    last_hit_s = time.time()

                    e = (header, type_names, path, filename)
                    for type_name in type_names:
                        if filter_predicate is not None and \
                           filter_predicate(type_name, e) is False:
                             self.__last_success_return = (type_name, e)
                             return
                        elif type_name in terminal_events:
                            raise TerminalEventException(type_name, e)

                    yield e

            if timeout_s is not None:
                time_since_event_s = time.time() - last_hit_s
                if time_since_event_s > timeout_s:
                    break

            if yield_nones is True:
                yield None

    @property
    def last_success_return(self):
        return self.__last_success_return


class _BaseTree(object):
    def __init__(self, logger, mask=external.PyInotify.inotify.constants.IN_ALL_EVENTS,
                 block_duration_s=_DEFAULT_EPOLL_BLOCK_DURATION_S):
        self.logger = logger
        
        # No matter what we actually received as the mask, make sure we have
        # the minimum that we require to curate our list of watches.
        self._mask = mask | \
                        external.PyInotify.inotify.constants.IN_ISDIR | \
                        external.PyInotify.inotify.constants.IN_CREATE | \
                        external.PyInotify.inotify.constants.IN_DELETE

        self._i = Inotify(logger, block_duration_s=block_duration_s)

    def _add_watch_and_sub_watches(self, path: str):
        self._i.add_watch(path, self._mask)
        for filename in os.listdir(path):
            entry_filepath = os.path.join(path, filename)
            if os.path.isdir(entry_filepath) == False:
                continue
            
            self._i.add_watch(entry_filepath, self._mask)
        
    def event_gen(self, ignore_missing_new_folders=False, **kwargs):
        """This is a secondary generator that wraps the principal one, and
        adds/removes watches as directories are added/removed.

        If we're doing anything funky and allowing the events to queue while a
        rename occurs then the folder may no longer exist. In this case, set
        `ignore_missing_new_folders`.
        """

        for event in self._i.event_gen(**kwargs):
            if event is not None:
                (header, type_names, path, filename) = event

                if header.mask & external.PyInotify.inotify.constants.IN_ISDIR:
                    full_path = os.path.join(path, filename)

                    if (
                        (header.mask & external.PyInotify.inotify.constants.IN_MOVED_TO) or
                        (header.mask & external.PyInotify.inotify.constants.IN_CREATE)
                       ) and \
                       (
                        os.path.exists(full_path) is True or
                        ignore_missing_new_folders is False
                       ):
                        self.logger.debug("A directory has been created. We're "
                                      "adding a watch on it (because we're "
                                      "being recursive): [%s]", full_path)

                        self._add_watch_and_sub_watches(full_path)

                    if header.mask & external.PyInotify.inotify.constants.IN_DELETE:
                        self.logger.debug("A directory has been removed. We're "
                                      "being recursive, but it would have "
                                      "automatically been deregistered: [%s]",
                                      full_path)

                        # The watch would've already been cleaned-up internally.
                        self._i.remove_watch_and_sub_watches(full_path)
                    elif header.mask & external.PyInotify.inotify.constants.IN_MOVED_FROM:
                        self.logger.debug("A directory has been renamed. We're "
                                      "being recursive, but it would have "
                                      "automatically been deregistered: [%s]",
                                      full_path)

                        self._i.remove_watch_and_sub_watches(full_path)
                    elif header.mask & external.PyInotify.inotify.constants.IN_MOVED_TO:
                        self.logger.debug("A directory has been renamed. We're "
                                      "adding a watch on it (because we're "
                                      "being recursive): [%s]", full_path)

                        self._add_watch_and_sub_watches(full_path)

            yield event

    @property
    def inotify(self):
        return self._i


class InotifyTree(_BaseTree):
    """Recursively watch a path."""

    def __init__(self, logger, path, mask=external.PyInotify.inotify.constants.IN_ALL_EVENTS,
                 block_duration_s=_DEFAULT_EPOLL_BLOCK_DURATION_S):
        super(InotifyTree, self).__init__(logger=logger, mask=mask, block_duration_s=block_duration_s)

        self.__root_path = path

        self.__load_tree(path)

    def __load_tree(self, path):
        self.logger.debug("Adding initial watches on tree: [%s]", path)

        paths = []

        q = [path]
        while q:
            current_path = q[0]
            del q[0]

            paths.append(current_path)

            for filename in os.listdir(current_path):
                entry_filepath = os.path.join(current_path, filename)
                if os.path.isdir(entry_filepath) is False:
                    continue

                q.append(entry_filepath)

        for path in paths:
            self._i.add_watch(path, self._mask)


class InotifyTrees(_BaseTree):
    """Recursively watch over a list of trees."""

    def __init__(self, logger, paths, mask=external.PyInotify.inotify.constants.IN_ALL_EVENTS,
                 block_duration_s=_DEFAULT_EPOLL_BLOCK_DURATION_S):
        super(InotifyTrees, self).__init__(logger=logger, mask=mask, block_duration_s=block_duration_s)

        self.__load_trees(paths)

    def __load_trees(self, paths):
        self.logger.debug("Adding initial watches on trees: [%s]", ",".join(map(str, paths)))

        found = []

        q = paths
        while q:
            current_path = q[0]
            del q[0]

            found.append(current_path)

            for filename in os.listdir(current_path):
                entry_filepath = os.path.join(current_path, filename)
                if os.path.isdir(entry_filepath) is False:
                    continue

                q.append(entry_filepath)


        for path in found:
            self._i.add_watch(path, self._mask)
