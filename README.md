# Video composer

Automatically cut and compose a video based on a CSV composition info.

## Installation

This software requires Python 3. See [Python's website](https://www.python.org/) for installation instructions.

When you have Python 3 installed, install required packages with pip (Python's package management system):

```
pip install listio
pip install moviepy
```

Then you can call the executable:

```
./video-composer -h
```

Or you can install this software as a Python package, which will also install all the dependencies and make the executable available globally:

```
python setup.py install

video-composer -h
```

## Usage

Create a CSV file describing the desired composition. Example:

my_composition.csv:

```
Dune.avi;00:12:24,677;00:12:40,860;"Leave us"
```

Then call:

```
video-composer -i my_composition.csv --intertitles
```

## Help

Call the executable mentioned in [Usage](#usage) with the parameter `-h` or `--help` to see full documentation. Example:

```
video-composer -h
```

## Contributing

__Feel free to remix this piece of software.__ See [NOTICE](./NOTICE) and [LICENSE](./LICENSE) for license information.
