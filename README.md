# Video Composer

Batch cut and compose video clips.

## Installation

1. Install [Python 3](https://www.python.org/).
2. Install Video Composer as a pip package:

```
pip install --user --upgrade .
```

This will make the executable `video-composer` available globally.

## Usage

Create a semicolon-separated CSV file describing the desired video clip
composition. Example:

my_composition.csv:

```
Dune.avi;00:12:24,677;00:12:40,860
Foo bar.mp4;01:00:03,000;01:05:00,000
```

Then call Video Composer:

```
video-composer --input my_composition.csv --clips src --output export
```

This will:

1. Search for video `Dune.avi` in directory `src`.
2. Cut a part from this video starting at time `00:12:24,677` and ending at
   `00:12:40,860`.
3. Render the cut clip into directory `export`.
4. Then the same will be done for the video `Foo bar.mp4`.

## Help

See the full list of available options:

```
video-composer -h
```

## Contributing

__Feel free to remix this piece of software.__ See [NOTICE](./NOTICE) and
[LICENSE](./LICENSE) for license information.
