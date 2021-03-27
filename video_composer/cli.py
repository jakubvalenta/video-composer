import argparse
import logging
import sys
from pathlib import Path

from video_composer import __title__
from video_composer.meta import DEFAULT_LIMIT, ClipMetas, Size
from video_composer.video import (
    DEFAULT_FPS, DEFAULT_INTERTITLE_COLOR, DEFAULT_INTERTITLE_DURATION,
    DEFAULT_INTERTITLE_FONT, DEFAULT_INTERTITLE_FONTSIZE,
    DEFAULT_INTERTITLE_POSITION, DEFAULT_SUFFIX, Composition,
)

logger = logging.getLogger(__name__)


class SizeAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, Size.from_string(values))


class FileSuffixAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        if type(values) == str and not values.startswith('.'):
            values = '.' + values
        setattr(namespace, self.dest, values)


class NotImplementedAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        parser.error('This option is not implemented yet')


def main():
    parser = argparse.ArgumentParser(prog=__title__)
    parser.add_argument(
        'csv',
        type=Path,
        nargs='?',
        help=(
            'CSV file with the list of source video paths and timestamps '
            'where to cut them'
        ),
    )
    parser.add_argument(
        '-i',
        '--input',
        type=Path,
        help='[DEPRECATED] Same as the positional argument CSV',
    )
    parser.add_argument(
        '-c',
        '--clips',
        type=Path,
        help=(
            'Directory where to look for the source video files; '
            'defaults to the current directory'
        ),
    )

    output_group = parser.add_mutually_exclusive_group(required=True)
    output_group.add_argument(
        '-o',
        '--output',
        dest='output_dir',
        type=Path,
        help=(
            'Write each output video as a separate file in this directory; '
            'Either --output or --join must be specified.'
        ),
    )
    output_group.add_argument(
        '-j',
        '--join',
        dest='output_file',
        type=Path,
        help=(
            'Join all output videos into this one video file; '
            'Either --output or --join must be specified.'
        ),
    )

    video_group = parser.add_argument_group('video format')
    video_group.add_argument(
        '-vf',
        '--video-fps',
        type=int,
        default=DEFAULT_FPS,
        help=f'Output video FPS; defaults to {DEFAULT_FPS}',
    )
    video_group.add_argument(
        '-ve',
        '--video-ext',
        default=DEFAULT_SUFFIX,
        action=FileSuffixAction,
        help=f'Output video file extension; defaults to {DEFAULT_SUFFIX}',
    )
    video_group.add_argument(
        '-vc',
        '--video-codec',
        help=(
            'Output video codec; defaults to not set, which means that '
            'moviepy will choose the codec automatically'
        ),
    )
    video_group.add_argument(
        '-vp',
        '--video-params',
        dest='ffmpeg_params',
        help=(
            'Additional FFmpeg parameters; '
            'example: --video-params="-vf eq=gamma=1.5"'
        ),
    )

    postprocessing_group = parser.add_argument_group('post-processing')
    postprocessing_group.add_argument(
        '-r',
        '--resize',
        action=SizeAction,
        help=(
            'Resize output video to passed size in format WIDTHxHEIGHT; '
            'example: --resize 1200x675'
        ),
    )
    postprocessing_group.add_argument(
        '-rw',
        '--resize-width',
        type=int,
        help='[DEPRECATED] Use --resize WIDTHxHEIGHT instead',
    )
    postprocessing_group.add_argument(
        '-rh',
        '--resize-height',
        type=int,
        help='[DEPRECATED] Use --resize WIDTHxHEIGHT instead',
    )
    postprocessing_group.add_argument(
        '-sp',
        '--speed',
        type=float,
        help=(
            'Change speed of the output video by factor; example: '
            '--speed 1: no change, '
            '--speed 0.5: half the normal speed, '
            '--speed 3: three times the normal speed'
        ),
    )
    postprocessing_group.add_argument(
        '-fd',
        '--fadeout',
        type=int,
        help=(
            'Duration of a fade-to-black effect at the end of each output '
            'video; defaults to 0 which means no fade-out'
        ),
    )

    subtitles_group = parser.add_argument_group('subtitles')
    subtitles_group.add_argument(
        '-sb',
        '--subtitles',
        type=Path,
        action=NotImplementedAction,
        help='[NOT IMPLEMENTED] Burn subtitles in the video',
    )

    intertitles_group = parser.add_argument_group('intertitles')
    intertitles_group.add_argument(
        '-it',
        '--intertitles',
        action='store_true',
        help='Prepend an intertitle to each output video',
    )
    intertitles_group.add_argument(
        '-ic',
        '--intertitle-color',
        default=DEFAULT_INTERTITLE_COLOR,
        help=f'Intertitle text color; defaults to {DEFAULT_INTERTITLE_COLOR}',
    )
    intertitles_group.add_argument(
        '-if',
        '--intertitle-font',
        default=DEFAULT_INTERTITLE_FONT,
        help=f'Intertitle font; defaults to {DEFAULT_INTERTITLE_FONT}',
    )
    intertitles_group.add_argument(
        '-is',
        '--intertitle-fontsize',
        type=int,
        default=DEFAULT_INTERTITLE_FONTSIZE,
        help=(
            'Intertitle font size in px; '
            f'defaults to {DEFAULT_INTERTITLE_FONTSIZE}'
        ),
    )
    intertitles_group.add_argument(
        '-ip',
        '--intertitle-position',
        default=DEFAULT_INTERTITLE_POSITION,
        help=f'Intertitle position; defaults to {DEFAULT_INTERTITLE_POSITION}',
    )
    intertitles_group.add_argument(
        '-id',
        '--intertitle-duration',
        type=int,
        default=DEFAULT_INTERTITLE_DURATION,
        help=(
            'Intertitle duration in seconds; '
            f'defaults to {DEFAULT_INTERTITLE_DURATION}'
        ),
    )

    debug_group = parser.add_argument_group('debugging')
    debug_group.add_argument(
        '-v', '--verbose', action='store_true', help='Enable verbose logging'
    )
    debug_group.add_argument(
        '-l',
        '--limit',
        type=int,
        default=DEFAULT_LIMIT,
        help=(
            'Process maximum this number of clips; '
            f'defaults to {DEFAULT_LIMIT} which means to process all clips'
        ),
    )

    args = parser.parse_args()
    if args.verbose:
        logging.basicConfig(
            stream=sys.stderr, level=logging.INFO, format='%(message)s'
        )
    if args.input:
        logger.warn(
            'Option --input is deprecated, use the positional argument CSV '
            'instead'
        )
        if not args.csv:
            args.csv = args.input
    if not args.csv:
        parser.error('The positional argument CSV is required')
    if args.resize_width or args.resize_height:
        logger.warn(
            'Options --resize-width and --resize-height are deprecated, '
            'use --resize instead'
        )
        if args.resize_width and args.resize_height:
            args.resize = Size(
                width=args.resize_width, height=args.resize_height
            )
        else:
            parser.error(
                'When using the deprecated options --resize-width and '
                '--resize-height, both of them have to be passed at the same'
                'time. Or use the new option --resize WIDTHxHEIGHT'
            )

    metas = ClipMetas.from_csv(args.csv, limit=args.limit)
    if args.clips:
        metas.add_base_path(args.clips)

    composition = Composition.from_metas(
        metas,
        fps=args.video_fps,
        suffix=args.video_ext,
        codec=args.video_codec,
        ffmpeg_params=args.ffmpeg_params.split(' ')
        if args.ffmpeg_params
        else (),
        tags=['i'] if args.intertitles else [],
    )

    for clip in composition.clips:
        clip.cut()
        if args.resize:
            clip.resize(width=args.resize.width, height=args.resize.height)
        if args.intertitles:
            clip.prepend_intertitle(
                color=args.intertitle_color,
                font=args.intertitle_font,
                fontsize=args.intertitle_fontsize,
                position=args.intertitle_position,
                duration=args.intertitle_duration,
            )
        if args.fadeout:
            clip.fadeout(duration=args.fadeout)
        if args.speed:
            clip.speed(factor=args.speed)

    if args.output_file:
        composition.render_joined(args.output_file)
    else:
        composition.render_split(args.output_dir)


if __name__ == '__main__':
    main()
