import logging
import os.path
import re

logger = logging.getLogger(__name__)


def _ensure_dir(path):
    path_dir, _ = os.path.split(path)
    if path_dir and not os.path.isdir(path_dir):
        os.makedirs(path_dir, exist_ok=True)


def _change_path_ext(path, ext):
    base, _ = os.path.splitext(path)
    return base + ext


def _format_duration(duration):
    return duration.replace(':', '_').replace('.', '_')


def _sanitize_path(s):
    return re.sub(r'[\w\d]', s, '_')[:64]


def format_clip_file_path(clip, dir_name, params=None, add_text=False):
    base_path, ext = os.path.splitext(clip.file_path)
    new_path = os.path.join(dir_name, base_path)
    start = _format_duration(clip.cut_start)
    end = _format_duration(clip.cut_end)
    params_str = '+'.join([''] + params) if params else ''
    text = '-' + _sanitize_path(clip.text) if add_text and clip.text else ''
    return f'{new_path}-{start}-{end}{text}{params_str}{ext}'


def render(video_clip, path, ext, dry_run, video_params, **kwargs):
    _ensure_dir(path)
    out_path = _change_path_ext(path, ext)
    if os.path.exists(out_path):
        logger.warn(f'Aborting rendering, output file "{out_path}" exists.')
        return
    if video_params:
        kwargs['ffmpeg_params'] = video_params.split(' ')
    if dry_run:
        logger.warn(f'Dry run write_videofile("{out_path}", **{kwargs})')
    else:
        logger.info(f'Rendering write_videofile("{out_path}", **{kwargs})')
        video_clip.write_videofile(out_path, **kwargs)
