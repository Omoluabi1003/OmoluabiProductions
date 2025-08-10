#!/bin/bash
set -euo pipefail

ffmpeg -y -loop 1 -i "ChatGPT Image Aug 10, 2025, 12_03_00 AM.png" -i New_Project.mp3 -c:v libx264 -c:a aac -shortest -pix_fmt yuv420p output.mp4
