# MediaInfo

MediaInfo is a Python wrapper library for `ffprobe` to provide a clean, developer-friendly API for developers to use when inspecting media files.

This project is licensed under the GNU General Public License version 3 (GPLv3).

`ffprobe` must be installed and in PATH to use this library. Installing `ffmpeg` usually includes `ffprobe`.

This library is still in development, but is stable enough for general use.

## Features

- Video and audio stream inspection
- Computed helpers for resolution, aspect ratio, FPS, bitrate, etc.
- Access to raw ffprobe output
- Extensible stream system
- Multi-stream media support

## Example Usage

```sh
python -m pip install pytmg-mediainfo
```

```python
from mediainfo import MediaInfo

fileinfo = MediaInfo("example.mp4")

print(fileinfo.streams.video.codec_name)
print(fileinfo.streams.video.resolution)
print(f"{fileinfo.streams.audio.samplerate_khz} kHz ({fileinfo.streams.audio.samplerate_category})")
```

## Links

- Python Package Index: https://pypi.org/project/pytmg-mediainfo/
- GitHub: https://github.com/pytmg/mediainfo