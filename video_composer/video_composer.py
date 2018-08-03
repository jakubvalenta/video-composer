import logging
import os
import re
import sys
from collections import namedtuple
from functools import partial, reduce

import listio
from moviepy.editor import concatenate_videoclips

from .filters import (filter_add_intertitle, filter_add_subtitles,
                      filter_adjust_speed, filter_fadeout, filter_resize,
                      filter_set_fps, filter_subclip, load_video_clip)

DEBUG_SKIP = ()
DEFAULT_LIMIT = -1

DEFAULT_FPS = 24
DEFAULT_EXT = '.mp4'
DEFAULT_CLIP_DIR = 'clips'

DEFAULT_TEXT_COLOR = 'white'
DEFAULT_TEXT_FONT = 'Arial'
DEFAULT_SUBTITLE_FONTSIZE = 36
DEFAULT_INTERTITLE_FONTSIZE = 48
DEFAULT_INTERTITLE_POSITION = 'center'
DEFAULT_INTERTITLE_DURATION = 3

DEFAULT_CSV_DELIMITER = ','

logger = logging.getLogger(__name__)


def _ensure_dir(path):
    path_dir, _ = os.path.split(path)
    if path_dir and not os.path.isdir(path_dir):
        os.makedirs(path_dir, exist_ok=True)


def _change_path_ext(path, ext):
    base, _ = os.path.splitext(path)
    return base + ext


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


def _parse_duration(duration):
    return duration.replace(',', '.')


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


Clip = namedtuple(
    'Clip',
    ['file_path', 'cut_start', 'cut_end', 'text'])


def read_clips(file_path, clips_dir, delimiter, limit):
    composition = listio.read_map(file_path, delimiter=delimiter)
    if not composition:
        logger.error('Exiting, no composition information found')
        sys.exit(1)
    for i, line in enumerate(composition):
        if i == limit:
            logger.warn(f'Limit {limit} reached')
            break
        if len(line) < 3:
            logger.warn(f'Skipping, invalid composition line "{line}"')
            continue
        raw_file_path, raw_cut_start, raw_cut_end = line[:3]
        file_path = os.path.join(clips_dir, raw_file_path)
        logger.info(f'Clip {i} "{file_path}"')
        if raw_file_path in DEBUG_SKIP:
            logger.warn('Skipping, clip found in DEBUG_SKIP')
            continue
        if not os.path.isfile(file_path):
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
        yield Clip(file_path, cut_start, cut_end, text)


def create_video_clips(clips, args):
    for clip in clips:
        video_clip = load_video_clip(clip.file_path)
        if args.resize_width and args.resize_height:
            intertitle_size_w = args.resize_width
            intertitle_size_h = args.resize_height
        else:
            intertitle_size_w = video_clip.w
            intertitle_size_h = video_clip.h
        filters = [
            partial(filter_subclip, start=clip.cut_start, end=clip.cut_end),
            partial(filter_set_fps, fps=args.video_fps),
            partial(
                filter_resize,
                width=args.resize_width,
                height=args.resize_height),
            partial(filter_add_subtitles, subtitles_path=args.subtitles),
            partial(
                filter_add_intertitle,
                intertitles=args.intertitles,
                text=clip.text,
                color=args.intertitle_color,
                font=args.intertitle_font,
                fontsize=args.intertitle_fontsize,
                position=args.intertitle_position,
                duration=args.intertitle_duration,
                width=intertitle_size_w,
                height=intertitle_size_h),
            partial(filter_adjust_speed, factor=args.speed),
            partial(filter_fadeout, duration=args.fadeout),
        ]
        video_clip = reduce(lambda acc, func: func(acc), filters, video_clip)
        yield clip, video_clip


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='TV Series Tools: Video'
    )
    parser.add_argument('--input', '-i', dest='inputfile', required=True,
                        help='file path to a file containing info on how to'
                        ' cut the clips')
    parser.add_argument('--clips', '-c', dest='clipsdir', required=True,
                        help='clips video files location')
    parser.add_argument('--output', '-o', dest='outputdir', required=True,
                        help='directory name inside --clips directory in which'
                        ' the cut clips will be rendered, or path to a single'
                        ' output video file if --join is set')
    parser.add_argument('--join', '-j', dest='join', action='store_true',
                        help='concat cut video clips')
    parser.add_argument('--video-fps', '-vf', dest='video_fps', type=int,
                        help='video fps, defaults to {}'
                        .format(DEFAULT_FPS),
                        default=DEFAULT_FPS)
    parser.add_argument('--video-ext', '-ve', dest='video_ext',
                        help='video file extension, defaults to {}'
                        .format(DEFAULT_EXT),
                        default=DEFAULT_EXT)
    parser.add_argument('--video-codec', '-vc', dest='video_codec',
                        help='video codec, defaults to not set, which means'
                        ' that moviepy will choose the codec automatically')
    parser.add_argument('--video-params', '-vp', dest='video_params',
                        help='additional parameters for FFmpeg,'
                        ' example: --video-params="-vf eq=gamma=1.5"')
    parser.add_argument('--resize-width', '-rw', dest='resize_width',
                        type=int,
                        help='resize width; you must set both --resize-width'
                        ' and --resize-height')
    parser.add_argument('--resize-height', '-rh', dest='resize_height',
                        type=int,
                        help='resize height; you must set both --resize-width'
                        ' and --resize-height')
    parser.add_argument('--limit', '-l', dest='limit', type=int,
                        default=DEFAULT_LIMIT,
                        help='process only first <limit> clips')
    parser.add_argument('--speed', '-sp', dest='speed', type=float,
                        help='speed of the composition; the standard speed'
                        ' will be multiplied by this number, hence'
                        ' 1 = normal speed, 0.5 = half the normal speed,'
                        ' 3 = three times as fast, etc.')
    parser.add_argument('--subtitles', '-sb', dest='subtitles',
                        action='store_true',
                        help='render subtitles')
    parser.add_argument('--intertitles', '-it', dest='intertitles',
                        action='store_true',
                        help='render itertitles')
    parser.add_argument('--intertitle-color', '-ic', dest='intertitle_color',
                        default=DEFAULT_TEXT_COLOR,
                        help='itertitle color; default \'{}\''
                        .format(DEFAULT_TEXT_COLOR))
    parser.add_argument('--intertitle-font', '-if', dest='intertitle_font',
                        default=DEFAULT_TEXT_FONT,
                        help='itertitle font; default \'{}\''
                        .format(DEFAULT_TEXT_FONT))
    parser.add_argument('--intertitle-fontsize', '-is',
                        dest='intertitle_fontsize', type=int,
                        default=DEFAULT_INTERTITLE_FONTSIZE,
                        help='itertitle font size in px; default \'{}\''
                        .format(DEFAULT_INTERTITLE_FONTSIZE))
    parser.add_argument('--intertitle-position', '-ip',
                        dest='intertitle_position',
                        default=DEFAULT_INTERTITLE_POSITION,
                        help='itertitle position; default \'{}\''
                        .format(DEFAULT_INTERTITLE_POSITION))
    parser.add_argument('--intertitle-duration', '-id',
                        dest='intertitle_duration', type=int,
                        default=DEFAULT_INTERTITLE_DURATION,
                        help='itertitle duration in seconds; default \'{}\''
                        .format(DEFAULT_INTERTITLE_DURATION))
    parser.add_argument('--fadeout', '-fd', dest='fadeout', type=int,
                        help='duration in milliseconds of a fadeout after each'
                        ' clip; defaults to 0 meaning no fadeout')
    parser.add_argument('--csv-delimiter', '-cd', dest='csv_delimiter',
                        help=('custom CSV delimiter; '
                              f'defaults to "{DEFAULT_CSV_DELIMITER}"'),
                        default=DEFAULT_CSV_DELIMITER)
    parser.add_argument('--filename-add-text', '-nt', dest='filename_add_text',
                        action='store_true',
                        help=('when --join is not set, add clip text to the '
                              'output filename of each clip'))
    parser.add_argument('--verbose', '-v', dest='verbose', action='store_true',
                        help='verbose output')
    parser.add_argument('--dry-run', '-d', dest='dry_run', action='store_true',
                        help='dry run')
    args = parser.parse_args()
    if args.verbose:
        logging.basicConfig(
            stream=sys.stdout,
            level=logging.INFO,
            format='%(message)s')
    render_kwargs = {
        'ext': args.video_ext,
        'dry_run': args.dry_run,
        'video_params': args.video_params,
        'fps': args.video_fps,
        'codec': args.video_codec,
    }
    clips = read_clips(
        args.inputfile,
        args.clipsdir,
        delimiter=args.csv_delimiter,
        limit=args.limit)
    clips_and_video_clips = create_video_clips(clips, args)
    if args.join:
        _, video_clips = zip(*clips_and_video_clips)
        joined_clip = concatenate_videoclips(video_clips)
        render(joined_clip, args.outputdir, **render_kwargs)
    else:
        for clip, video_clip in clips_and_video_clips:
            params = []
            if args.intertitles:
                params.append('i')
            clip_path = format_clip_file_path(
                clip,
                args.outputdir,
                params=params,
                add_text=args.filename_add_text)
            render(video_clip, clip_path, **render_kwargs)


if __name__ == '__main__':
    main()
