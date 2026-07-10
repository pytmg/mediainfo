# MediaInfo

MediaInfo is a Python wrapper library for `ffprobe` to provide a clean, developer-friendly API for developers to use when inspecting media files.

This project is protected under version 3 of the GNU General Public License.

You require `ffprobe` installed, and in your PATH. You can install `ffmpeg` for your system, which includes `ffprobe`.

## Example Usage

```python
from mediainfo import MediaInfo

fileinfo = MediaInfo("example.mp4")

print(info.streams.video.codec_name)
print(info.streams.video.resolution)
print(f"{info.streams.audio.samplerate_khz} kHz ({info.streams.audio.samplerate_preset})")
```

https://pypi.org/project/pytmg-mediainfo/
https://github.com/pytmg/mediainfo