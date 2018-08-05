import logging
import sys
from functools import partial, reduce

from moviepy.editor import concatenate_videoclips
from video_composer import filters, reader, renderer

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
DEFAULT_CLIP_PATH_TEMPLATE = (
    '${output_path}/${clips_dir}/${clip_path}/'
    '${clip_file}-${start}-${end}${text}${params}${ext}')

logger = logging.getLogger(__name__)


def _call_all(funcs, val):
    return reduce(lambda acc, func: func(acc), funcs, val)


def create_video_clips(clips, args):
    for clip in clips:
        video_clip = filters.load_video_clip(clip.full_path)
        if args.resize_width and args.resize_height:
            intertitle_size_w = args.resize_width
            intertitle_size_h = args.resize_height
        else:
            intertitle_size_w = video_clip.w
            intertitle_size_h = video_clip.h
        funcs = [
            partial(
                filters.filter_subclip,
                start=clip.cut_start,
                end=clip.cut_end),
            partial(
                filters.filter_set_fps,
                fps=args.video_fps),
            partial(
                filters.filter_resize,
                width=args.resize_width,
                height=args.resize_height),
            partial(
                filters.filter_add_subtitles,
                subtitles_path=args.subtitles),
            partial(
                filters.filter_add_intertitle,
                intertitles=args.intertitles,
                text=clip.text,
                color=args.intertitle_color,
                font=args.intertitle_font,
                fontsize=args.intertitle_fontsize,
                position=args.intertitle_position,
                duration=args.intertitle_duration,
                width=intertitle_size_w,
                height=intertitle_size_h),
            partial(
                filters.filter_adjust_speed,
                factor=args.speed),
            partial(
                filters.filter_fadeout,
                duration=args.fadeout),
        ]
        video_clip = _call_all(funcs, video_clip)
        yield clip, video_clip


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Video Composer')
    parser.add_argument('--input', '-i', dest='input_file', required=True,
                        help='file path to a file containing info on how to'
                        ' cut the clips')
    parser.add_argument('--clips', '-c', dest='clips_dir', required=True,
                        help='clips video files location')
    parser.add_argument(
        '--output', '-o',
        dest='output_path', required=True,
        help=('directory in which clips will be rendered when --join is false '
              'or path to output video file when --join is true'))
    parser.add_argument(
        '--output-clip-path-template', '-of',
        dest='output_clip_path_template',
        help=('output path template of an individual clip; '
              'applies only when --join is not set; '
              f'defaults to {DEFAULT_CLIP_PATH_TEMPLATE}'),
        default=DEFAULT_CLIP_PATH_TEMPLATE)
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
    clips = reader.read_clips(
        args.input_file,
        args.clips_dir,
        delimiter=args.csv_delimiter,
        limit=args.limit,
        skip=DEBUG_SKIP)
    clips_and_video_clips = create_video_clips(clips, args)
    if args.join:
        _, video_clips = zip(*clips_and_video_clips)
        joined_clip = concatenate_videoclips(video_clips)
        renderer.render(joined_clip, args.output_path, **render_kwargs)
    else:
        for clip, video_clip in clips_and_video_clips:
            params = []
            if args.intertitles:
                params.append('i')
            clip_path = renderer.format_clip_path(
                args.output_clip_path_template,
                clip,
                args.output_path,
                args.clips_dir,
                params)
            renderer.render(video_clip, clip_path, **render_kwargs)


if __name__ == '__main__':
    main()
