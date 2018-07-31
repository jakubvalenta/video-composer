import logging
from collections import namedtuple

from moviepy.editor import CompositeVideoClip, TextClip, concatenate_videoclips
from moviepy.video.tools.subtitles import SubtitlesClip

logger = logging.getLogger(__name__)

Resize = namedtuple('Resize', ['w', 'h', 'x', 'y'])


def subtitle_generator(txt):
    return TextClip(txt, font='Georgia-Regular', fontsize=24, color='white')


def generate_text_clip(text, width, color, font, fontsize):
    text_with_line_breaks = text.replace('|', '\n')
    return TextClip(
        text_with_line_breaks,
        size=(width, None),
        color=color,
        font=font,
        fontsize=fontsize,
        method='caption',
        align='center')


def _calc_resize(current_width, current_height, width, height):
    current_aspect_ratio = current_width / current_height
    new_aspect_ratio = width / height
    clip_x = 0
    clip_y = 0
    if new_aspect_ratio > current_aspect_ratio:
        new_width = width
        new_height = round(new_width / current_aspect_ratio)
        clip_y = (new_height - height) / 2
    elif new_aspect_ratio < current_aspect_ratio:
        new_height = height
        new_width = round(new_height * current_aspect_ratio)
        clip_x = (new_width - width) / 2
    else:
        new_width = width
        new_height = height
    return Resize(new_width, new_height, clip_x, clip_y)


def filter_resize(video_clip, width, height):
    if not width and not height:
        return video_clip
    if video_clip.w == width and video_clip.h == height:
        logger.info('Resizing not necessary')
        return video_clip
    resize = _calc_resize(video_clip.w, video_clip.h, width, height)
    logger.info(f'Resizing from {video_clip.w} x {video_clip.h} '
                f'to {resize.w} x {resize.h}')
    video_clip = video_clip.resize((resize.w, resize.h))
    if resize.x > 0 or resize.y > 0:
        logger.info(f'Cropping +{resize.x}+{resize.y}')
        video_clip = video_clip.crop(
            x1=resize.x,
            y1=resize.y,
            width=width,
            height=height)
    return video_clip


def filter_add_subtitles(video_clip, subtitles_path):
    subtitles_clip = SubtitlesClip(
        subtitles_path,
        subtitle_generator)
    return CompositeVideoClip([video_clip, subtitles_clip])


def filter_add_intertitle(
        video_clip,
        text,
        color,
        font,
        fontsize,
        position,
        duration,
        width,
        height,
        text_width_factor=0.8):
    text_clip = generate_text_clip(
        text,
        width * text_width_factor,
        color=color,
        font=font,
        fontsize=fontsize)
    composite_clip = CompositeVideoClip(
        [text_clip.set_pos(position)],
        (width, height))
    intertitle_clip = composite_clip.subclip(0, duration)
    return concatenate_videoclips(
        [intertitle_clip, video_clip],
        method='compose')


def filter_fadeout(video_clip, duration):
    return video_clip.fadeout(duration/1000)


def filter_adjust_speed(video_clip, factor):
    return video_clip.speedx(factor=factor)
