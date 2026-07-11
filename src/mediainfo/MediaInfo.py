# MediaInfo - A Python wrapper around ffprobe
# Copyright (C) 2026 pytmg
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the license or
# (at your option) any later version

"""
MediaInfo.py

A Python wrapper around ffprobe.

This project is currently in development, but is considered stable enough
for general use. Deprecated features are removed in minor releases.

Current deprecations will be removed in V0.2.0.
"""

import os, shutil, subprocess, json, math
from typing_extensions import deprecated
from typing import Literal
from types import SimpleNamespace

class Exceptions:
    class MediaInfoBaseError(Exception):
        """MediaInfo base error"""
        pass

    class FFProbeBaseError(Exception):
        """FFProbe base error"""
        pass

    class FFProbeNotFoundError(FFProbeBaseError):
        """ffprobe executable not found"""
        pass

    class MediaInfoMissingProperties(MediaInfoBaseError):
        """Missing properties for stream"""
        pass

    class MediaInfoCannotReadJSON(MediaInfoBaseError):
        """JSON cannot be decoded."""
        pass

class Format:
    """
    Format information.
    """
    def __init__(self, d):
        self.filename = d["filename"]
        self.nb_streams = d["nb_streams"]
        self.nb_programs = d["nb_programs"]
        self.format_name = d["format_name"]
        self.format_long_name = d["format_long_name"]
        self.start_time = d["start_time"]
        self.duration: float = float(d["duration"])
        self.size = d["size"]
        self.bit_rate = d["bit_rate"]
        self.probe_score = d["probe_score"]
        self.tags = d["tags"] # tags is just another dict buuut who cares anyway
    
    @property
    def duration_s(self) -> float:
        """
        Alias for builtin duration
        """
        return self.duration
    
    @property
    def duration_str(self) -> str:
        """
        Computed from builtin duration
        Duration in a formatted string.
        """
        seconds = int(self.duration)
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours:
            return f"{hours}h {minutes}m {seconds}s"
        if minutes:
            return f"{minutes}m {seconds}s"
        return f"{seconds}s"

class Stream:
    """
    Base stream class, extend from this if you're making your own streams, like captions or others that aren't already included.
    """
    def __init__(self, d):
        self.index: int = d["index"]
        self.codec_type: str = d["codec_type"]
        self.codec_name: str = d["codec_name"]

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} codec_name='{self.codec_name}' codec_type='{self.codec_type}'>"

class VideoStream(Stream):
    """
    The video stream's information, doesn't include data.

    Has helper properties.
    """
    def __init__(self, d):
        super().__init__(d)
        self.codec_long_name: str = d["codec_long_name"]
        self.profile: str = d["profile"]
        self.codec_tag_string: str = d["codec_tag_string"]
        self.codec_tag: str = d["codec_tag"]
        self.mime_codec_string: str = d["mime_codec_string"]
        self.width: int = d["width"]
        self.height: int = d["height"]
        self.coded_width: int = d["coded_width"]
        self.coded_height: int = d["coded_height"]
        self.has_b_frames: bool = d["has_b_frames"] == 1 # has_b_frames is either 0 or 1
        self.sample_aspect_ratio: str = d["sample_aspect_ratio"]
        self.pix_fmt: str = d["pix_fmt"]
        self.level: int = d["level"]
        self.color_range: str = d["color_range"]
        self.color_space: str = d["color_space"]
        self.color_transfer: str = d["color_transfer"]
        self.color_primaries: str = d["color_primaries"]
        self.id: str = d["id"] # the one i was looking at was 0x2 so i wouldnt know if it was just an int or str or sum
        self.r_frame_rate: float = float(d["r_frame_rate"].split("/")[0]) / float(d["r_frame_rate"].split("/")[1])
        self.avg_frame_rate: float = float(d["avg_frame_rate"].split("/")[0]) / float(d["avg_frame_rate"].split("/")[1])
        self.time_base: float = float(d["time_base"].split("/")[0]) / float(d["time_base"].split("/")[1])
        self.start_pts: float | int = d["start_pts"] # int, float, idk
        self.start_time: float = float(d["start_time"])
        self.duration_ts: float | int = d["duration_ts"] # int, float, idk, depends on the video
        self.bit_rate: int = int(d["bit_rate"])
        self.nb_frames: int = int(d["nb_frames"])
        self.extradata_size: int = d["extradata_size"]
        self.disposition = SimpleNamespace(**d["disposition"]) # doesnt get used by much, use __dict__ if unsure
        self.tags = SimpleNamespace(**d["tags"]) # same thing

    @property
    def is_portrait(self) -> bool:
        """
        Computed from builtins width and height
        Is this video taller than it is wide?
        """
        return self.height > self.width
    
    @property
    def is_landscape(self) -> bool:
        """
        Computed from builtins width and height
        Is this video wider than it is tall?
        """
        return self.width > self.height
    
    @property
    def is_square(self) -> bool:
        """
        Computed from builtins width and height
        Is this video.. a square?
        """
        return self.width == self.height
    
    @property
    def aspect_category(self) -> Literal["square", "portrait", "landscape"]:
        """
        Computed from is_portrait, is_landscape and is_square
        """
        if self.is_square:
            return "square"
        if self.is_portrait:
            return "portrait"
        return "landscape"
    
    @property
    def aspect_ratio_value(self) -> float:
        """
        Computed from builtins width and height
        Not to be confused with builtin sample_aspect_ratio
        """
        return self.width / self.height
    
    @property
    def aspect_ratio(self) -> str:
        """
        Computed from builtins width and height
        Provides human readable aspect ratio, e.g. 16:9, 4:3, 1:1, etc.
        """
        g = math.gcd(self.width, self.height)
        return f"{self.width // g}:{self.height // g}"
    
    @property
    def resolution(self) -> str:
        """
        Computed from builtins width and height
        """
        return f"{self.width}x{self.height}"
    
    @property
    def pixels(self) -> int:
        """
        Computed from builtins width and height
        Does not provide the pixel data, just how many there are.
        """
        return self.width * self.height
    
    @property
    def fps(self) -> float:
        """
        Computed from builtin avg_frame_rate
        """
        return round(self.avg_frame_rate, 2)
    
    @property
    def duration(self) -> str:
        """
        Computed from builtins duration_ts and time_base
        Duration in a formatted string.
        """
        seconds = int(self.duration_ts * self.time_base)
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours:
            return f"{hours}h {minutes}m {seconds}s"
        if minutes:
            return f"{minutes}m {seconds}s"
        return f"{seconds}s"
    
    @property
    def duration_s(self) -> float:
        """
        Computed from builtins duration_ts and time_base
        Duration in seconds.
        """
        return self.duration_ts * self.time_base
    
    @property
    def megapixels(self) -> float:
        """
        Computed from pixels
        """
        return round(self.pixels / 1_000_000, 2)
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} resolution='{self.resolution}' fps={self.fps} codec_name='{self.codec_name}'>"
    
class AudioStream(Stream):
    """
    The audio stream's information, doesn't include data.

    Has helper properties.
    """
    def __init__(self, d):
        super().__init__(d)
        self.codec_long_name: str = d["codec_long_name"]
        self.codec_tag_string: str = d["codec_tag_string"]
        self.codec_tag: str = d["codec_tag"]
        self.mime_codec_string: str = d["mime_codec_string"]
        self.sample_fmt: str = d["sample_fmt"]
        self.sample_rate: int = int(d["sample_rate"]) # if you tell me its a float i will crash out
        self.channels: int = d["channels"]
        self.channel_layout: str = d["channel_layout"]
        self.bits_per_sample: int = d["bits_per_sample"]
        self.initial_padding: int = d["initial_padding"]
        # there was the same framerate bullshit as video so i just cut it cuz its all 0
        self.id: str = d["id"] # the one i was looking at was 0x2 so i wouldnt know if it was just an int or str or sum
        self.time_base: float = float(d["time_base"].split("/")[0]) / float(d["time_base"].split("/")[1])
        self.start_pts: float | int = d["start_pts"] # int, float, idk
        self.start_time: float = float(d["start_time"])
        self.duration_ts: float | int = d["duration_ts"] # int, float, idk, depends on the video
        self.bit_rate: int = int(d["bit_rate"])
        self.nb_frames: int = int(d["nb_frames"])
        self.extradata_size: int = d["extradata_size"]
        self.disposition = SimpleNamespace(**d["disposition"]) # doesnt get used by much, use __dict__ if unsure
        self.tags = SimpleNamespace(**d["tags"]) # same thing

    @property
    def samplerate_category(self) -> str:
        """
        Computed from builtin sample_rate
        """
        presets = {
            8000: "Telephone",
            11025: "Quarter CD",
            16000: "Speech",
            22050: "AM Radio",
            32000: "FM Radio",
            44100: "CD",
            48000: "DVD",
            96000: "Hi-Res",
            192000: "Ultra Hi-Res"
        }
        return presets.get(self.sample_rate, "Custom")
    
    @property
    def channels_category(self) -> str:
        """
        Computed from builtin channels
        """
        presets = {
            1: "Mono",
            2: "Stereo",
            3: "2.1",
            4: "Quad",
            6: "5.1",
            8: "7.1"
        }
        return presets.get(self.channels, "Custom")
    
    @property
    def bitrate_category(self) -> str:
        """
        Computed from builtin bit_rate
        """
        presets = {
            0: "Very Compressed",
            32000: "Voice",
            96000: "Compressed",
            192000: "High Quality",
            320000: "Very High Quality"
        }
        highestthres = presets[0]
        for key, value in presets.items():
            if self.bit_rate < key:
                return highestthres
            highestthres = value

    @property
    def bitrate_kbps(self) -> float:
        """
        Computed from builtin bit_rate
        """
        return round(self.bit_rate / 1000, 1)
    
    @property
    def samplerate_khz(self) -> float:
        """
        Computed from builtin sample_rate
        """
        return round(self.sample_rate / 1000, 1)
    
    @property
    def duration_s(self) -> float:
        """
        Computed from builtins duration_ts and time_base
        Duration in seconds.
        """
        return self.duration_ts * self.time_base
    
    @property
    def duration(self) -> str:
        """
        Computed from builtins duration_ts and time_base
        Duration in a formatted string.
        """
        seconds = int(self.duration_ts * self.time_base)
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours:
            return f"{hours}h {minutes}m {seconds}s"
        if minutes:
            return f"{minutes}m {seconds}s"
        return f"{seconds}s"
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} samplerate_khz={self.samplerate_khz} channels={self.channels} codec_name='{self.codec_name}'>"

class Streams:
    """
    Streams information.

    Can be subclassed to add custom stream types as additional properties.
    Subclasses should preserve the collection attributes.
    """
    def __init__(self, d):
        self.all: list[Stream] = []
        self.raw: list[dict] = d
        try:
            self.process_stream("video", VideoStream)
            self.process_stream("audio", AudioStream)
        except KeyError as e:
            raise Exceptions.MediaInfoMissingProperties(f"Missing stream property. KeyErr: {e}")
        
    def process_stream(self, codec_type: str, stream_class: type[Stream]) -> list[Stream]:
        """
        Process more stream types, useful when extending.

        Parameters:
            codec_type (str): The codec type, can be "video", "audio", "subtitle", etc
            stream_class (type[Stream]): The class of the stream you're processing. Class must be based off Stream.

        Returns:
            list[Stream]: A list of the processed streams.
        """
        processed = []
        for stream in self.raw:
            if stream["codec_type"] == codec_type:
                obj = stream_class(stream)
                self.all.append(obj)
                processed.append(obj)
        return processed

    @property
    def videos(self) -> list[VideoStream]:
        """
        All video streams
        """
        videos = []
        for stream in self.all:
            if isinstance(stream, VideoStream):
                videos.append(stream)
        return videos

    @property
    def audios(self) -> list[AudioStream]:
        """
        All audio streams
        """
        audios = []
        for stream in self.all:
            if isinstance(stream, AudioStream):
                audios.append(stream)
        return audios

    @property
    def video(self) -> VideoStream | None:
        """
        Computed from videos
        First video stream
        """
        try:
            return self.videos[0]
        except IndexError:
            return None

    @property
    def audio(self) -> AudioStream | None:
        """
        Computed from audios
        First audio stream
        """
        try:
            return self.audios[0]
        except IndexError:
            return None

    @property
    @deprecated("use .all instead")
    def allstreams(self) -> list[Stream]:
        return self.all

class MediaInfo:
    """
    A wrapper around ffprobe, an ffmpeg builtin.
    """
    def __init__(self, file):

        path = os.path.abspath(os.path.expandvars(os.path.expanduser(file)))

        if not os.path.exists(path):
            raise FileNotFoundError(f"File {file} does not exist.")
        
        if not shutil.which("ffprobe"):
            raise Exceptions.FFProbeNotFoundError("FFProbe not found in PATH. Install FFmpeg (which includes ffprobe) and add it to PATH.")

        r = subprocess.run(["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", path],
            capture_output = True, text = True)

        self.path = path
        try:
            self.dict = json.loads(r.stdout)
        except json.JSONDecodeError:
            raise Exceptions.MediaInfoCannotReadJSON("Invalid JSON, cannot be decoded.")

        self.streams = Streams(self.dict["streams"])
        self.format = Format(self.dict["format"])

    def __repr__(self):
        return f"<{self.__class__.__name__} file='{os.path.basename(self.path)}' streams={len(self.streams.all)}>"

    def __str__(self):
        String = f"{repr(self)}"
        if not self.streams.video:
            String += "\nVideo: none"
        if not self.streams.audio:
            String += "\nAudio: none"

        for stream in self.streams.all:
            if isinstance(stream, VideoStream):
                String += f"\nStream #{stream.index}: Video: {stream.codec_name} {stream.resolution} {stream.fps}"
            if isinstance(stream, AudioStream):
                String += f"\nStream #{stream.index}: Audio: {stream.codec_name} {stream.samplerate_khz}kHz {stream.channels_category}"
        
        String += f"\nDuration: {self.format.duration_str}"

        return String