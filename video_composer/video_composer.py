import csv
import math
import os
import sys

from moviepy.editor import *
from moviepy.video.tools.subtitles import SubtitlesClip
import listio


DEBUG_SKIP = ()
DEFAULT_LIMIT = -1

DEFAULT_FPS = 24
DEFAULT_EXT = '.avi'
DEFAULT_CODEC = {
    '.avi': 'png',
}
DEFAULT_CLIP_DIR = 'clips'

DEFAULT_TEXT_COLOR = 'white'
DEFAULT_TEXT_FONT = 'Arial'
DEFAULT_SUBTITLE_FONTSIZE = 36
DEFAULT_INTERTITLE_FONTSIZE = 48
DEFAULT_INTERTITLE_POSITION = 'center'
DEFAULT_INTERTITLE_DURATION = 3


def render(clip, file_path, fps=None, ext=None, codec=None):
    if fps is None:
        fps = DEFAULT_FPS
    if ext is None:
        ext = DEFAULT_EXT
    dir, _ = os.path.split(file_path)
    if dir and not os.path.isdir(dir):
        os.makedirs(dir)
    base, _ = os.path.splitext(file_path)
    if codec is None and ext in DEFAULT_CODEC:
        codec = DEFAULT_CODEC[ext]
    clip.write_videofile(base + ext, fps=fps, codec=codec)


def generate_text_clip(text, color=None, font=None, fontsize=None):
    if color is None:
        color = DEFAULT_TEXT_COLOR
    if font is None:
        font = DEFAULT_TEXT_FONT
    if fontsize is None:
        fontsize = DEFAULT_TEXT_FONTSIZE
    return TextClip(text, color=color, font=font, fontsize=fontsize)


def subtitle_generator(txt):
    return TextClip(txt, font='Georgia-Regular', fontsize=24, color='white')


def parse_duration(duration):
    return duration.replace(',', '.')


def format_duration(duration):
    return duration.replace(':', '_').replace('.', '_')


def format_clip_file_path(file_path, dir_name, cut_start, cut_end):
    file_dir, file_basename = os.path.split(file_path)
    file_name, file_ext = os.path.splitext(file_basename)
    new_path_without_ext = os.path.join(file_dir, dir_name, file_name)
    return '{path}-{start}-{end}{ext}'.format(
        path=new_path_without_ext,
        start=format_duration(cut_start),
        end=format_duration(cut_end),
        ext=file_ext
    )


def filter_add_subtitles(video_clip, subtitles_path):
    subtitles_clip = SubtitlesClip(
        subtitles_path,
        generate_text_clip
    )
    return CompositeVideoClip([video_clip, subtitles_clip])


def filter_add_intertitle(video_clip, text, color, font, fontsize, position,
                          duration, width, height):
    text_clip = generate_text_clip(
        text,
        color,
        font,
        fontsize
    )
    composite_clip = CompositeVideoClip(
        [text_clip.set_pos(position)],
        (width, height)
    )
    intertitle_clip = composite_clip.subclip(0, duration)
    return concatenate_videoclips([intertitle_clip, video_clip])


def filter_adjust_speed(video_clip, factor):
    return video_clip.speedx(factor=factor)


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
    parser.add_argument('--output', '-o', dest='outputfile', required=True,
                        help='directory name inside --clips directory in which'
                        ' the cut clips will be rendered, or path to a single'
                        ' output video file if --join is set')
    parser.add_argument('--join', '-j', dest='join', action='store_true',
                        help='concat cut video clips')
    parser.add_argument('--change-fps', '-f', dest='change_fps', type=int,
                        default=DEFAULT_FPS,
                        help='video fps')
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
                        dest='intertitle_fontsize',
                        default=DEFAULT_INTERTITLE_FONTSIZE,
                        help='itertitle font size in px; default \'{}\''
                        .format(DEFAULT_INTERTITLE_FONTSIZE))
    parser.add_argument('--intertitle-position', '-ip',
                        dest='intertitle_position',
                        default=DEFAULT_INTERTITLE_POSITION,
                        help='itertitle position; default \'{}\''
                        .format(DEFAULT_INTERTITLE_POSITION))
    parser.add_argument('--intertitle-duration', '-id',
                        dest='intertitle_duration',
                        default=DEFAULT_INTERTITLE_DURATION,
                        help='itertitle duration in seconds; default \'{}\''
                        .format(DEFAULT_INTERTITLE_DURATION))
    args = parser.parse_args()

    composition = listio.read_map(args.inputfile)
    if not composition:
        sys.exit(1)

    all_clips = []

    cache_video_clips = {}
    for i, composition in enumerate(composition):
        if i == args.limit:
            print('LIMIT {} HIT'.format(args.limit))
            break

        file_path = os.path.join(args.clipsdir, composition[0])
        cut_start = parse_duration(composition[1])
        cut_end = parse_duration(composition[2])
        print(
            'CLIP {}\n'
            '  {}\n'
            '  {} --> {}'
            .format(
                i,
                file_path,
                cut_start,
                cut_end
            )
        )

        if composition[0] in DEBUG_SKIP:
            print('  SKIP clip found in DEBUG_SKIP list')
            continue
        if not os.path.isfile(file_path):
            print('  SKIP file not found')
            continue
        if not args.join:
            clip_file_path = format_clip_file_path(
                file_path, args.outputfile, cut_start, cut_end
            )
            if os.path.isfile(clip_file_path):
                print('  SKIP clip exists')
                continue

        if file_path not in cache_video_clips:
            cache_video_clips[file_path] = VideoFileClip(file_path)
        video_clip = cache_video_clips[file_path]

        video_sub_clip = video_clip.subclip(cut_start, cut_end)
        if args.change_fps:
            video_sub_clip = video_sub_clip.set_fps(args.change_fps)
        if args.resize_width and args.resize_height:
            video_sub_clip = video_sub_clip.resize(
                width=args.resize_width, height=args.resize_height
            )

        composite_clip = video_sub_clip
        if args.subtitles:
            composite_clip = filter_add_subtitles(
                composite_clip,
                subtitles_path
            )
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
                intertitle_size_h
            )
        if args.speed:
            composite_clip = filter_adjust_speed(
                composite_clip,
                args.speed
            )

        if args.join:
            all_clips.append(composite_clip)
        else:
            render(composite_clip, clip_file_path, fps=args.change_fps)

    if args.join:
        joined_clip = concatenate_videoclips(all_clips)
        render(joined_clip, args.outputfile, fps=args.change_fps)

    sys.exit()


if __name__ == '__main__':
    main()
