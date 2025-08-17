# OmoluabiProductions

This repository contains the assets for "Take The Risk":

- `Take The Risk.png` – cover art
- `Take The Risk.mp3` – audio track

## Regenerate the video

You can recreate the `Take The Risk.mp4` video using ffmpeg. The generated video
is ignored by git to keep the repository lightweight:

```bash
ffmpeg -loop 1 -i "Take The Risk.png" -i "Take The Risk.mp3" -c:v libx264 -tune stillimage -c:a copy -shortest -pix_fmt yuv420p "Take The Risk.mp4"
```
