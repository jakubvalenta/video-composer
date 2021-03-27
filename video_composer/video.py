import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional, Sequence

from moviepy.editor import (
    CompositeVideoClip, TextClip, VideoFileClip, concatenate_videoclips,
)
from moviepy.video.tools.subtitles import SubtitlesClip

from video_composer.meta import ClipMeta, Size

logger = logging.getLogger(__name__)

DEFAULT_FPS = 24
DEFAULT_SUFFIX = '.mp4'

DEFAULT_INTERTITLE_COLOR = 'white'
DEFAULT_INTERTITLE_DURATION = 3
DEFAULT_INTERTITLE_FONT = 'Arial'
DEFAULT_INTERTITLE_FONTSIZE = 36
DEFAULT_INTERTITLE_FONTSIZE = 48
DEFAULT_INTERTITLE_POSITION = 'center'

DEFAULT_SUBTITLE_FONT = 'Georgia-Regular'
DEFAULT_SUBTITLE_FONTSIZE = 24
DEFAULT_SUBTITLE_COLOR = 'white'

INTERTITLE_TEXT_WIDTH_FACTOR = 0.8


class Clip:
    _cache: dict[Path, VideoFileClip] = {}

    def __init__(self, meta: ClipMeta):
        self.meta = meta
        if meta.path not in Clip._cache:
            Clip._cache[meta.path] = VideoFileClip(str(meta.path))
        self.video_file_clip = Clip._cache[meta.path]

    def cut(self):
        if self.meta.start is not None and self.meta.end is not None:
            logger.info(
                '%s: Cutting %s -> %s',
                self.meta.path,
                self.meta.start,
                self.meta.end,
            )
            self.video_file_clip = self.video_file_clip.subclip(
                self.meta.start.total_seconds(), self.meta.end.total_seconds()
            )

    def set_fps(self):
        self.video_file_clip = self.video_file_clip.set_fps(self.video_fps)

    def resize(self, width: int, height: int):
        current_width = self.video_file_clip.w
        current_height = self.video_file_clip.h
        current_aspect_ratio = current_width / current_height
        new_aspect_ratio = width / height
        if current_width == width and current_height == height:
            logger.info('%s: Resizing not necessary', self.meta.path)
            return
        crop_x: float = 0
        crop_y: float = 0
        if new_aspect_ratio > current_aspect_ratio:
            new_width: float = width
            new_height: float = round(new_width / current_aspect_ratio)
            crop_y = (new_height - height) / 2
        elif new_aspect_ratio < current_aspect_ratio:
            new_height = height
            new_width = round(new_height * current_aspect_ratio)
            crop_x = (new_width - width) / 2
        else:
            new_width = width
            new_height = height

        logger.info(
            '%s: Resizing from %f x %f [%f] to %f x %f [%f] ',
            self.meta.path,
            current_width,
            current_height,
            current_aspect_ratio,
            new_width,
            new_height,
            new_aspect_ratio,
        )
        self.video_file_clip = self.video_file_clip.resize(
            (new_width, new_height)
        )

        if crop_x > 0 or crop_y > 0:
            logger.info(
                '%s: Cropping +%f+%f',
                self.meta.path,
                crop_x,
                crop_y,
            )
            self.video_file_clip = self.video_file_clip.crop(
                x1=crop_x, y1=crop_y, width=width, height=height
            )

    def add_subtitles(
        self,
        subtitles_path: Path,
        color: str = DEFAULT_SUBTITLE_COLOR,
        font: str = DEFAULT_SUBTITLE_FONT,
        fontsize: int = DEFAULT_SUBTITLE_FONTSIZE,
    ):
        """Currently unused"""

        def subtitle_text_clip_factory(text: str) -> TextClip:
            return TextClip(text, font, fontsize, color)

        subtitles_clip = SubtitlesClip(
            subtitles_path, subtitle_text_clip_factory
        )
        self.video_file_clip = CompositeVideoClip(
            [self.video_file_clip, subtitles_clip]
        )

    def prepend_intertitle(
        self,
        size: Optional[Size] = None,
        color: str = DEFAULT_INTERTITLE_COLOR,
        font: str = DEFAULT_INTERTITLE_FONT,
        fontsize: int = DEFAULT_INTERTITLE_FONTSIZE,
        position: str = DEFAULT_INTERTITLE_POSITION,
        duration: int = DEFAULT_INTERTITLE_DURATION,
    ):
        if not self.meta.text:
            logger.warning('%s: Missing intertitle text')
            return
        logger.info('%s: Intertitle "%s"', self.meta.path, self.meta.text)
        if not size:
            size = Size(
                width=self.video_file_clip.w, height=self.video_file_clip.h
            )
        text_clip = TextClip(
            self.meta.text.replace('|', '\n'),
            size=(size.width * INTERTITLE_TEXT_WIDTH_FACTOR, None),
            color=color,
            font=font,
            fontsize=fontsize,
            method='caption',
            align='center',
        )
        composite_clip = CompositeVideoClip(
            [text_clip.set_pos(position)], (size.width, size.height)
        )
        intertitle_clip = composite_clip.subclip(0, duration)
        self.video_file_clip = concatenate_videoclips(
            [intertitle_clip, self.video_file_clip], method='compose'
        )

    def fadeout(self, duration: float):
        self.video_file_clip = self.video_file_clip.fadeout(duration / 1000)

    def speed(self, factor: float):
        self.video_file_clip = self.video_file_clip.speedx(factor=factor)


@dataclass
class Composition:
    clips: list[Clip]
    fps: int = DEFAULT_FPS
    suffix: str = DEFAULT_SUFFIX
    codec: Optional[str] = None
    ffmpeg_params: Sequence[str] = ()
    tags: Sequence[str] = ()

    @classmethod
    def from_metas(cls, metas: Iterable[ClipMeta], **kwargs) -> 'Composition':
        clips = []
        for i, meta in enumerate(metas):
            logger.info('%d %s', i + 1, meta.path)
            if meta.path.is_file():
                clips.append(Clip(meta))
            else:
                logger.warn('%s: Source video file doesn\'t exist', meta.path)
        return cls(clips=clips, **kwargs)

    def _render_video_file_clip(
        self, video_file_clip: VideoFileClip, output_file_path: Path
    ):
        output_file_path.parent.mkdir(parents=True, exist_ok=True)
        video_file_clip.write_videofile(
            str(output_file_path),
            fps=self.fps,
            codec=self.codec,
            ffmpeg_params=self.ffmpeg_params,
        )

    def render_split(self, output_dir_path: Path):
        for clip in self.clips:
            output_file_path = output_dir_path / clip.meta.get_output_path(
                suffix=self.suffix, tags=self.tags
            )
            if output_file_path.exists():
                logger.warn(
                    '%s: Output file "%s" exists',
                    clip.meta.path,
                    output_file_path,
                )
                continue
            self._render_video_file_clip(
                clip.video_file_clip, output_file_path
            )

    def render_joined(self, output_file_path: Path):
        if not self.video_file_clips:
            logger.warn('Nothing to do, the composition has no clips')
            return
        self._render_video_file_clip(
            concatenate_videoclips(self.video_file_clips),
            output_file_path,
        )

    @property
    def video_file_clips(self) -> list[VideoFileClip]:
        return [clip.video_file_clip for clip in self.clips]
