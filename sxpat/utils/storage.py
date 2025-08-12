from typing import Any, Dict, List, NoReturn, Union
from bidict import bidict

import itertools as it
import copy
import csv


class LiveStorage:
    """
        Represents a live storage on which data can be staged and then committed.  
        The class uses a stack to store staged data,
        the first stage after a commit pops all data above the staged key.

        The class has guards to prevent restaging data without committing or staging out of order
        (a key cannot be added before others that appeared sooner in previous staging sequences).
        A commit with missing keys (actually missing, not implicitly copied from the previous iteration) is valid.

        This class can be used with a context manager and will automatically save on exit.

        @authors: Marco Biasion
    """

    _NC_ERR_MSG = 'Key `{key}` was restaged without a commit.'
    _OOO_ERR_MSG = (
        '`{key}`(index:{idx}) was staged in the wrong order '
        '(must be after `{last_key}`(index:{last_idx})).'
    )

    def __init__(self, save_destination: str):
        self._stack: Dict[str, Any] = dict()
        """Contains the staged data."""
        self._storage: List[Dict[str, Any]] = list()
        """Contains all committed data."""

        self._order: bidict[str, int] = bidict()
        """Records the order of the keys."""
        self._last_index_set: int = -1
        """Records the latest index that was set. -1 if no new stages after a commit."""

        self._destination = save_destination
        """Name of the file that will contain the storage when exiting."""
        self._save_from: int = 0
        """Starting index in `_storage` a `save()` call sould save."""

    def stage(self, **kwargs: Any) -> None:
        # loop in order through all new key/value pairs
        for (key, value) in kwargs.items():
            # add key to _order if first occurrence
            if key not in self._order:
                self._order[key] = len(self._order)

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

    def commit(self):
        """Commits the current stack."""

        # add stack to storage
        self._storage.append(copy.deepcopy(self._stack))
        # reset latest index
        self._last_index_set = -1

    def ignore(self):
        """
            Ignores the current stack.
            This method has the same side effects as `.commit()` but without actually committing the stack.
        """

        # reset latest index
        self._last_index_set = -1

    def save(self) -> None:
        """
            Writes all the commited data in `csv` format to the file described by `save_destination`,
            the data is appended if the file was created by a previous save of this object, it is overwritten otherwise.

            Skips all data which was already saved, so multiple calls do not duplicate data.
        """

        # skip if there is no data to save
        if self._save_from == len(self._storage): return

        # select opening mode depending on if it is the first save or not
        wanted_mode = 'w' if self._save_from == 0 else 'a'
        with open(self._destination, wanted_mode) as ofile:
            writer = csv.DictWriter(ofile, self._order.keys())

            # write header if it is the first save
            if self._save_from == 0: writer.writeheader()

            writer.writerows(it.islice(self._storage, self._save_from, None, None))

        # update starting index for next save
        self._save_from = len(self._storage)

    def _check_out_of_order(self, key: str) -> Union[None, NoReturn]:
        if self._last_index_set == -1: return
        if (idx := self._order[key]) <= self._last_index_set:
            raise self.OutOfOrderStageError(self._OOO_ERR_MSG.format(
                key=key,
                idx=idx,
                last_key=self._order.inverse[self._last_index_set],
                last_idx=self._last_index_set,
            ))

    def _check_restaged_without_commit(self, key: str) -> Union[None, NoReturn]:
        if key in self._stack and self._last_index_set != -1:
            raise self.KeyRestagedWithoutCommitError(self._NC_ERR_MSG.format(
                key=key,
            ))

    def __enter__(self): return self
    def __exit__(self, _0, _1, _2): self.save()

    class StageError(Exception): """Base class for data staging errors."""
    class KeyRestagedWithoutCommitError(StageError): """An already present key was staged without the previous data being committed."""
    class OutOfOrderStageError(StageError): """A key was staged out of order."""
