import logging
import os.path
import re
from string import Template

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


def format_clip_path(template_str, clip, output_path, clips_dir, params):
    clip_path, clip_basename = os.path.split(clip.orig_path)
    clip_file, ext = os.path.splitext(clip_basename)
    start = _format_duration(clip.cut_start)
    end = _format_duration(clip.cut_end)
    text = '-' + _sanitize_path(clip.text)
    params_str = '+'.join([''] + params) if params else ''
    s = Template(template_str)
    return s.safe_substitute(
        output_path=output_path,
        clips_dir=clips_dir,
        clip_path=clip_path,
        clip_file=clip_file,
        start=start,
        end=end,
        text=text,
        params=params_str,
        ext=ext)


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
