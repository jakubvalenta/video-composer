import datetime
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import IO, Optional, Sequence

import listio

logger = logging.getLogger(__name__)

DEFAULT_LIMIT = -1


def safe_filename(s: str) -> str:
    return re.sub(r'[^A-Za-z\d_-]', '_', s)


class CompositionError(Exception):
    pass


@dataclass
class Size:
    width: int
    height: int

    @classmethod
    def from_string(cls, s: str) -> 'Size':
        width, height = map(int, s.split('x'))
        return cls(width=width, height=height)


class Timestamp(datetime.timedelta):
    @classmethod
    def from_string(cls, s: str) -> Optional['Timestamp']:
        m = re.match(
            r'^(?P<h>\d{2}):(?P<m>\d{2}):(?P<s>\d{2})[\.,](?P<ms>\d{3})$',
            s,
        )
        if not m:
            return None
        return cls(
            hours=int(m.group('h')),
            minutes=int(m.group('m')),
            seconds=int(m.group('s')),
            milliseconds=int(m.group('ms')),
        )

    def __str__(self) -> str:
        h, rest = divmod(self.seconds, 3600)
        m, rest = divmod(rest, 60)
        s = rest // 1
        ms = self.microseconds // 1000
        return f'{h:02.0f}:{m:02.0f}:{s:02.0f}.{ms:03.0f}'


@dataclass
class ClipMeta:
    path: Path
    start: Optional[Timestamp]
    end: Optional[Timestamp]
    text: Optional[str]

    @classmethod
    def from_row(cls, row: list[str]) -> 'ClipMeta':
        path = Path(row[0])
        return cls(
            path=path,
            start=Timestamp.from_string(row[1]),
            end=Timestamp.from_string(row[2]),
            text=row[3] if len(row) > 3 else None,
        )

    def get_output_path(self, suffix: str, tags: Sequence[str]) -> Path:
        params_str = f'+{"+".join(tags)}' if tags else ''
        start_str = f'-{self.start}' if self.start else ''
        end_str = f'-{self.end}' if self.end else ''
        return self.path.with_stem(
            safe_filename(
                ''.join([self.path.stem, start_str, end_str, params_str])
            )
        ).with_suffix(suffix)


class ClipMetas(list):
    @classmethod
    def from_csv(cls, f: IO, limit: int = DEFAULT_LIMIT) -> 'ClipMetas':
        rows = listio.read_map(f)
        if not rows:
            raise CompositionError('Input CSV file is empty')
        metas = []
        for i, row in enumerate(rows):
            if i == limit:
                logger.info('Reached limit %d', limit)
                break
            metas.append(ClipMeta.from_row(row))
        return cls(metas)
