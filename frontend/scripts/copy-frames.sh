#!/bin/bash

# Copy frames from /tmp/frames to public/frames
mkdir -p /vercel/share/v0-project/public/frames
cp /tmp/frames/*.jpg /vercel/share/v0-project/public/frames/

echo "Copied 192 frames to public/frames"
