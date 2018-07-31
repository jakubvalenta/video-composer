import logging
import os
import sys

import listio
from moviepy.editor import VideoFileClip, concatenate_videoclips

from .filters import (filter_add_intertitle, filter_adjust_speed,
                      filter_fadeout, filter_resize)

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


def render(clip, path, ext, *args, **kwargs):
    _ensure_dir(path)
    out_path = _change_path_ext(path, ext)
    if os.path.exists(out_path):
        logger.warn(f'Aborting rendering, output file "{out_path}" exists.')
        return False
    logger.info(f'  Rendering to "{out_path}".')
    clip.write_videofile(out_path, *args, **kwargs)
    return True


def parse_duration(duration):
    return duration.replace(',', '.')


def format_duration(duration):
    return duration.replace(':', '_').replace('.', '_')


def format_clip_file_path(
        file_path,
        dir_name,
        cut_start,
        cut_end,
        ext,
        params=None):
    file_dir, file_basename = os.path.split(file_path)
    file_name, _ = os.path.splitext(file_basename)
    new_path_without_ext = os.path.join(file_dir, dir_name, file_name)
    if params:
        params_str = '+'.join([''] + params)
    else:
        params_str = ''
    return '{path}-{start}-{end}{params_str}{ext}'.format(
        path=new_path_without_ext,
        start=format_duration(cut_start),
        end=format_duration(cut_end),
        params_str=params_str,
        ext=ext)


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
    args = parser.parse_args()

    if args.video_params:
        ffmpeg_params = args.video_params.split(' ')
    else:
        ffmpeg_params = []
    render_kwargs = {
        'fps': args.video_fps,
        'codec': args.video_codec,
        'ffmpeg_params': ffmpeg_params,
    }

    composition = listio.read_map(args.inputfile, delimiter=args.csv_delimiter)
    if not composition:
        print('Exiting, no composition information found')
        sys.exit(1)

    all_clips = []

    cache_video_clips = {}
    for i, composition in enumerate(composition):
        if i == args.limit:
            print('LIMIT {} HIT'.format(args.limit))
            break

        file_path = os.path.join(args.clipsdir, composition[0])
        print('CLIP {} "{}"'.format(i, file_path))
        if len(composition) < 3 or not composition[1] or not composition[2]:
            print('  SKIP no cut defined')
            continue
        cut_start = parse_duration(composition[1])
        cut_end = parse_duration(composition[2])
        print('  CUT {} --> {}'.format(cut_start, cut_end))

        if composition[0] in DEBUG_SKIP:
            print('  SKIP clip found in DEBUG_SKIP list')
            continue
        if not os.path.isfile(file_path):
            print('  SKIP file not found')
            continue
        if not args.join:
            params = []
            if args.intertitles:
                params.append('i')
            clip_file_path = format_clip_file_path(
                file_path,
                args.outputdir,
                cut_start,
                cut_end,
                ext=args.video_ext,
                params=params)

        if file_path not in cache_video_clips:
            cache_video_clips[file_path] = VideoFileClip(file_path)
        video_clip = cache_video_clips[file_path]

        if cut_start and cut_end:
            video_sub_clip = video_clip.subclip(cut_start, cut_end)
        else:
            video_sub_clip = video_clip
        if args.video_fps:
            video_sub_clip = video_sub_clip.set_fps(args.video_fps)

        composite_clip = video_sub_clip
        composite_clip = filter_resize(
            composite_clip,
            args.resize_width,
            args.resize_height)
        if args.subtitles:
            raise NotImplementedError
            # TODO: Figure out what subtitles path should be.
            # composite_clip = filter_add_subtitles(
            #     composite_clip,
            #     subtitles_path)
        if args.intertitles:
            text = composition[3]
            print('  INTERTITLE {}'.format(text))
            if args.resize_width and args.resize_height:
                intertitle_size_w = args.resize_width
                intertitle_size_h = args.resize_height
            else:
                intertitle_size_w = composite_clip.w
                intertitle_size_h = composite_clip.h
            composite_clip = filter_add_intertitle(
                composite_clip,
                text,
                args.intertitle_color,
                args.intertitle_font,
                args.intertitle_fontsize,
                args.intertitle_position,
                args.intertitle_duration,
                intertitle_size_w,
                intertitle_size_h)
        if args.speed:
            composite_clip = filter_adjust_speed(
                composite_clip,
                args.speed)
        if args.fadeout:
            composite_clip = filter_fadeout(
                composite_clip,
                args.fadeout)

        if args.join:
            all_clips.append(composite_clip)
        else:
            render(
                composite_clip,
                clip_file_path,
                args.video_ext,
                **render_kwargs)

    if args.join:
        joined_clip = concatenate_videoclips(all_clips)
        render(joined_clip, args.outputdir, args.video_ext, **render_kwargs)


if __name__ == '__main__':
    main()
