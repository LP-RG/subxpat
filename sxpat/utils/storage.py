from typing import Any, Mapping, NoReturn, Self, Union
from bidict import bidict

import csv
import copy
import itertools as it


__all__ = ['LiveStorage', 'AppendStorage']


class LiveStorage:
    """
        Represents a live storage on which data can be staged and then committed.  
        The class uses a stack to store staged data,
        the first stage after a commit pops all data above the restaged key.

        The class has guards to prevent restaging data without committing or staging out of order
        (a key cannot be added before others that appeared sooner in previous staging sequences).
        A commit with missing keys (actually missing, not implicitly copied from the previous iteration) is **valid**.

        The unerlying file is kept updated as new keys and rows are added.

        This class can be used with a context manager and will automatically flush on exit.

        :authors: Marco Biasion
    """

    def __init__(
        self,
        save_destination: str,
    ):
        """
            :param save_destination: the path to open the file to.
            :raises FileExistsError: if the file already exists.
        """

        self._stack: dict[str, Any] = dict()
        """Contains the staged data."""
        self._order: bidict[str, int] = bidict()
        """Records the order of the keys."""
        self._last_index_set: int = -1
        """Records the latest index that was set. -1 if no new stages after a commit."""

        self._must_rewrite: bool = True
        """If the file should be rewritten from scratch."""
        self._storage: list[list[Any]] = list()
        """Contains all committed data."""
        self._file = open(save_destination, 'x')
        """File object that will contain the data."""
        self._writer = csv.writer(self._file, lineterminator='\n')
        """CSV Writer object to write to the file."""

    def stage(self, mapping: Mapping[str, Any] = dict(), /, **kwargs: Any) -> Self:
        """
            Stages all given values at their given key on the current stack.

            :param mapping: a dictionary like object containing keys and their associated values to stage.
            :param kwargs: keyword arguments, that will be staged under the keyword.
            :return: the storage object.
        """

        # loop in order through all new key/value pairs
        for (key, value) in it.chain(kwargs.items(), mapping.items()):
            # add key to _order if first occurrence
            if key not in self._order:
                self._order[key] = len(self._order)
                self._must_rewrite = True

            # guards
            self._check_out_of_order(key)
            self._check_restaged_without_commit(key)

            # pop from stack until key (included), if present
            if key in self._stack:
                while self._stack.popitem()[0] != key: pass

            # add to stack
            self._stack[key] = value
            # save latest index
            self._last_index_set = self._order[key]

        return self

    def commit(self):
        """Commits the current stack."""

        # add stack to storage (as list)
        self._storage.append([
            copy.deepcopy(v)
            for v in {
                **dict.fromkeys(self._order.keys()),  # required to correctly preserve missing keys
                **self._stack
            }.values()
        ])

        # write
        if self._must_rewrite:
            # reset file if needed
            self._file.seek(0, 0)
            self._writer.writerow(self._order.keys())
            # write all rows
            self._writer.writerows(self._storage)
        else:
            # write only last
            self._writer.writerow(self._storage[-1])

        # reset latest index
        self._last_index_set = -1

    def ignore(self):
        """
            Ignores the current stack.
            This method has the same side effects as `.commit()` but without actually committing the stack.
        """

        # reset latest index
        self._last_index_set = -1

    def flush(self): self._file.flush()
    def close(self): self._file.close()

    def _check_out_of_order(self, key: str) -> Union[None, NoReturn]:
        if self._last_index_set == -1: return
        if (idx := self._order[key]) <= self._last_index_set:
            raise self.OutOfOrderStageError(
                key,
                idx,
                self._order.inverse[self._last_index_set],
                self._last_index_set,
            )

    def _check_restaged_without_commit(self, key: str) -> Union[None, NoReturn]:
        if key in self._stack and self._last_index_set != -1:
            raise self.KeyRestagedWithoutCommitError(key)

    def __enter__(self): return self
    def __exit__(self, exc_type, exc, tb): self.flush()

    def __repr__(self) -> str: return f'{type(self).__qualname__}({self._file.name})'

    class StageError(Exception):
        """Base class for data staging errors."""

    class KeyRestagedWithoutCommitError(StageError):
        """An already present key was staged without the previous data being committed."""

        def __init__(self, key_name: str, *args):
            super().__init__(
                f'Key `{key_name}` was restaged without a commit.',
                *args
            )

    class OutOfOrderStageError(StageError):
        """A key was staged out of order."""

        def __init__(self, key: str, idx: int, last_key: str, last_idx: int, *args):
            super().__init__(
                (
                    f'`{key}`(index:{idx}) was staged in the wrong order'
                    f' (must be staged after `{last_key}`(index:{last_idx})).'
                ),
                *args
            )


class AppendStorage:
    """
        Represents a storage on which data can be appended to.

        The class has guards to prevent readding data with the same keys.

        This class can be used with a context manager and will automatically save on exit.

        :authors: Marco Biasion
    """

    def __init__(self, save_destination: str):
        #
        self._seen_keys = set()
        #
        self._file = open(save_destination, 'x')
        self._writer = csv.writer(self._file, lineterminator='\n')

    def add(self, mapping: Mapping[str, Any] = dict(), /, **kwargs: Any):
        # guard
        for key in it.chain(kwargs.keys(), mapping.keys()):
            if key in self._seen_keys: raise self.DuplicateKeyError(key)
            self._seen_keys.add(key)

        # write
        self._writer.writerows(it.chain(kwargs.items(), mapping.items()))

    def flush(self): self._file.flush()
    def close(self): self._file.close()

    def __enter__(self): return self
    def __exit__(self, exc_type, exc, tb): self.flush()

    class DuplicateKeyError(LookupError):
        """A key was trying to be readded."""

        def __init__(self, key: str, *args):
            super().__init__(f'duplicate key: {key}', *args)
