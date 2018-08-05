import logging
import os.path
from collections import namedtuple

import listio

logger = logging.getLogger(__name__)


Clip = namedtuple(
    'Clip',
    ['orig_path', 'full_path', 'cut_start', 'cut_end', 'text'])


def _parse_duration(duration):
    return duration.replace(',', '.')


def read_clips(csv_path, clips_dir, delimiter, limit=-1, skip=()):
    composition = listio.read_map(csv_path, delimiter=delimiter)
    if not composition:
        logger.error('Exiting, no composition information found')
        return None
    for i, line in enumerate(composition):
        if i == limit:
            logger.warn(f'Limit {limit} reached')
            break
        if len(line) < 3:
            logger.warn(f'Skipping, invalid composition line "{line}"')
            continue
        orig_path, raw_cut_start, raw_cut_end = line[:3]
        full_path = os.path.join(clips_dir, orig_path)
        logger.info(f'Clip {i} "{orig_path}"')
        if orig_path in skip:
            logger.warn('Skipping, clip found in the param `skip`')
            continue
        if not os.path.isfile(full_path):
            logger.warn('Skipping, file not found')
            continue
        if not raw_cut_start or not raw_cut_end:
            logger.warn('Skipping, no cut defined')
            continue
        cut_start = _parse_duration(raw_cut_start)
        cut_end = _parse_duration(raw_cut_end)
        logger.info(f'Cut {cut_start} --> {cut_end}')
        if len(line) > 3:
            text = line[3]
            logger.info(f'Text "{text}"')
        else:
            text = None
        yield Clip(orig_path, full_path, cut_start, cut_end, text)
