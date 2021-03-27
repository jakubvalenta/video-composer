# Video Composer

Batch cut and compose video clips.

Reads information about which video files to cut and at which timestamps from a
CSV spreadsheet.

Writes the cut clips either as separate files or joined in one video.

Uses [MoviePy](https://zulko.github.io/moviepy/index.html) under the hood.

## Installation

1. Install [Python >= 3.9](https://www.python.org/).

2. Install Video Composer as a pip package:

    ``` shell
    $ pip install -e .  # byexample: +pass
    ```

    This will make the executable `video-composer` available globally.

## Usage

### Input CSV spreadsheet

Video Composer takes a **semicolon-separated** CSV spreadsheet as its input. It
must have at least three columns:

- video file path
- timestamp where to start the cut; format:
  `<hours>:<minutes>:<seconds>.<milliseconds>`
- timestamp where to end the cut; format:
  `<hours>:<minutes>:<seconds>.<milliseconds>`

Optionally, a fourth column can be present:

- intertitle text

Empty lines and lines starting with `#` will be ignored.

Example:

``` csv
# my_composition.csv
foo.avi;00:12:24.677;00:12:40.860
bar/spam.mp4;01:00:03.000;01:05:00.000;"Intertitle text"
```

### Testing videos

Before going on with the usage examples, let's first generate two testing videos
and an input CSV spreadsheet.

``` shell
$ mkdir -p test  # byexample: +pass
$ cd test
$ [ -f testsrc.mpg ] || ffmpeg -f lavfi -i testsrc=duration=50:size=768x480:rate=25 testsrc.mpg  # byexample: +pass
$ [ -f smptebars.mp4 ] || ffmpeg -f lavfi -i smptebars=duration=50:size=768x480:rate=25 smptebars.mp4  # byexample: +pass
$ cat > input.csv <<EOF
> testsrc.mpg;00:00:05,200;00:00:08,900;"Foo!"
> smptebars.mp4;00:00:40,000;00:00:42,500;"Bar, spam..."
> EOF
```

### Basic usage

Cut each source video specified in the input CSV and render each output video as
a separate file:

``` shell
$ video-composer -v input.csv --output clips  # byexample: +pass
$ ls clips  # byexample: +norm-ws
smptebars-00_00_40_000-00_00_42_500.mp4
testsrc-00_00_05_200-00_00_08_900.mp4
```

Cut each source video specified in the input CSV and join all output videos as
one file:

``` shell
$ video-composer -v input.csv --join output.mp4  # byexample: +pass
$ ls output.mp4
output.mp4
```

If your source video files are in a different directory, use the option
`--clips` to specify their location:

``` shell
$ pushd .. > /dev/null
$ video-composer -v test/input.csv --join test/output2.mp4 --clips test  # byexample: +pass
$ popd > /dev/null
$ ls output2.mp4
output2.mp4
```

### Specifying video format

Use the `--video-ext` option to set the file extension of the file. Video
Composer will then choose the right video codec automatically.

``` shell
$ video-composer -v input.csv --video-ext webm --output clips_video_format  # byexample: +pass
$ ls clips_video_format  # byexample: +norm-ws
smptebars-00_00_40_000-00_00_42_500.webm
testsrc-00_00_05_200-00_00_08_900.webm
```

There are also more options to set the output video FPS, to set the video codec
explicitly and to pass additional parameters to FFmpeg.

``` shell
$ video-composer -v input.csv \
>                --video-fps 10 \
>                --video-ext foo.webm \
>                --video-codec vp8 \
>                --video-params="-vf eq=gamma=1.5" \
>                --output clips_video_format_advanced  # byexample: +pass
$ ls clips_video_format_advanced  # byexample: +norm-ws
smptebars-00_00_40_000-00_00_42_500.foo.webm
testsrc-00_00_05_200-00_00_08_900.foo.webm
```

### Posprocessing

Use the options `--resize`, `--speed` and `--fadeout` to postprocess the video.

When resizing the video, the video will be resized to cover the specified
frame. Anything part of the video that doesn't fit the frame due to difference
in aspect ratio will be cropped.

``` shell
$ video-composer -v input.csv \
>                --resize 300x300 \
>                --speed 0.5 \
>                --fadeout 5 \
>                --join output_postprocessed.mp4  # byexample: +pass
$ ls output_postprocessed.mp4
output_postprocessed.mp4
```

### Intertitles

Use the option `--intertitles` to prepend a intertitle clip to each output
video. The default is 5s black video with a white centered text in Arial.

The text is read from the fourth column of the input CSV spreadsheet.

``` shell
$ video-composer -v input.csv --intertitles --join output_intertitles.mp4  # byexample: +pass
$ ls output_intertitles.mp4
output_intertitles.mp4
```

You can also specify custom intertitle text color, font, font size, position and
duration.

``` shell
$ video-composer -v input.csv \
>                --intertitles \
>                --intertitle-color "#ff0000" \
>                --intertitle-font "DejaVu-Serif-Condensed" \
>                --intertitle-fontsize 96 \
>                --intertitle-position 'top' \
>                --intertitle-duration 5 \
>                --join output_intertitles_custom.mp4  # byexample: +pass
$ ls output_intertitles_custom.mp4
output_intertitles_custom.mp4
```

### More

See the full list of available options:

``` shell
$ video-composer -h  # byexample: +norm-ws +rm=~
usage: Video Composer [-h] [-i INPUT] [-c CLIPS]
                      (-o OUTPUT_DIR | -j OUTPUT_FILE) [-vf VIDEO_FPS]
                      [-ve VIDEO_EXT] [-vc VIDEO_CODEC] [-vp FFMPEG_PARAMS]
                      [-r RESIZE] [-rw RESIZE_WIDTH] [-rh RESIZE_HEIGHT]
                      [-sp SPEED] [-fd FADEOUT] [-sb SUBTITLES] [-it]
                      [-ic INTERTITLE_COLOR] [-if INTERTITLE_FONT]
                      [-is INTERTITLE_FONTSIZE] [-ip INTERTITLE_POSITION]
                      [-id INTERTITLE_DURATION] [-v] [-l LIMIT]
                      [csv]
~
positional arguments:
  csv                   CSV file with the list of source video paths and
                        timestamps where to cut them
~
optional arguments:
  -h, --help            show this help message and exit
  -i INPUT, --input INPUT
                        [DEPRECATED] Same as the positional argument CSV
  -c CLIPS, --clips CLIPS
                        Directory where to look for the source video files;
                        defaults to the current directory
  -o OUTPUT_DIR, --output OUTPUT_DIR
                        Write each output video as a separate file in this
                        directory; Either --output or --join must be
                        specified.
  -j OUTPUT_FILE, --join OUTPUT_FILE
                        Join all output videos into this one video file;
                        Either --output or --join must be specified.
~
video format:
  -vf VIDEO_FPS, --video-fps VIDEO_FPS
                        Output video FPS; defaults to 24
  -ve VIDEO_EXT, --video-ext VIDEO_EXT
                        Output video file extension; defaults to .mp4
  -vc VIDEO_CODEC, --video-codec VIDEO_CODEC
                        Output video codec; defaults to not set, which means
                        that moviepy will choose the codec automatically
  -vp FFMPEG_PARAMS, --video-params FFMPEG_PARAMS
                        Additional FFmpeg parameters; example: --video-
                        params="-vf eq=gamma=1.5"
~
post-processing:
  -r RESIZE, --resize RESIZE
                        Resize output video to passed size in format
                        WIDTHxHEIGHT; example: --resize 1200x675
  -rw RESIZE_WIDTH, --resize-width RESIZE_WIDTH
                        [DEPRECATED] Use --resize WIDTHxHEIGHT instead
  -rh RESIZE_HEIGHT, --resize-height RESIZE_HEIGHT
                        [DEPRECATED] Use --resize WIDTHxHEIGHT instead
  -sp SPEED, --speed SPEED
                        Change speed of the output video by factor; example:
                        --speed 1: no change, --speed 0.5: half the normal
                        speed, --speed 3: three times the normal speed
  -fd FADEOUT, --fadeout FADEOUT
                        Duration of a fade-to-black effect at the end of each
                        output video; defaults to 0 which means no fade-out
~
subtitles:
  -sb SUBTITLES, --subtitles SUBTITLES
                        [NOT IMPLEMENTED] Burn subtitles in the video
~
intertitles:
  -it, --intertitles    Prepend an intertitle to each output video
  -ic INTERTITLE_COLOR, --intertitle-color INTERTITLE_COLOR
                        Intertitle text color; defaults to white
  -if INTERTITLE_FONT, --intertitle-font INTERTITLE_FONT
                        Intertitle font; defaults to Arial
  -is INTERTITLE_FONTSIZE, --intertitle-fontsize INTERTITLE_FONTSIZE
                        Intertitle font size in px; defaults to 48
  -ip INTERTITLE_POSITION, --intertitle-position INTERTITLE_POSITION
                        Intertitle position; defaults to center
  -id INTERTITLE_DURATION, --intertitle-duration INTERTITLE_DURATION
                        Intertitle duration in seconds; defaults to 3
~
debugging:
  -v, --verbose         Enable verbose logging
  -l LIMIT, --limit LIMIT
                        Process maximum this number of clips; defaults to -1
                        which means to process all clips
```

### Deprecated options

These options are deprecated but available for compatibility with previous
version of Video Composer:

``` shell
$ video-composer -v -i input.csv -rw 300 -rh 300 --join output_deprecated_options.mp4  # byexample: +pass
```

### Not implemented yet

These options are not implemented yet:

``` shell
$ video-composer -v input.csv --subtitles test_subtitles.srt --join output_subtitles.mp4 || true  # byexample: +pass
```

## Development

### Installation

``` shell
$ make setup-dev  # byexample: +skip
```

### Testing and linting

``` shell
$ make test  # byexample: +skip
$ make lint  # byexample: +skip
$ make byexample  # byexample: +skip
```

### Help

``` shell
$ make help  # byexample: +skip
```

## Contributing

__Feel free to remix this piece of software.__ See [NOTICE](./NOTICE) and
[LICENSE](./LICENSE) for license information.
