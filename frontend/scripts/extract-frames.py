#!/usr/bin/env python3
import cv2
import os
import urllib.request
import sys

VIDEO_URL = 'https://hebbkx1anhila5yf.public.blob.vercel-storage.com/Desk_transforming_into_202603290128-irMNNgLKr6LDSWpWAB7imMk9jHUdT5.mp4'
TEMP_VIDEO = '/tmp/temp_video.mp4'
OUTPUT_DIR = '/tmp/frames'
FPS = 30

def extract_frames():
    try:
        # Create output directory
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        print(f"Created output directory: {OUTPUT_DIR}")

        # Download video
        print("Downloading video...")
        urllib.request.urlretrieve(VIDEO_URL, TEMP_VIDEO)
        print("Video downloaded.")

        # Open video with OpenCV
        print(f"Extracting frames at {FPS} fps...")
        cap = cv2.VideoCapture(TEMP_VIDEO)
        
        if not cap.isOpened():
            print("Error: Could not open video file")
            return
        
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        video_fps = int(cap.get(cv2.CAP_PROP_FPS))
        frame_interval = max(1, video_fps // FPS)
        
        print(f"Video has {total_frames} frames at {video_fps} fps")
        print(f"Frame interval: {frame_interval}")
        
        frame_count = 0
        extracted_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            if frame_count % frame_interval == 0:
                filename = os.path.join(OUTPUT_DIR, f'frame_{extracted_count:04d}.jpg')
                cv2.imwrite(filename, frame)
                extracted_count += 1
                
                if extracted_count % 10 == 0:
                    print(f"Extracted {extracted_count} frames...")
            
            frame_count += 1
        
        cap.release()
        
        print(f"\nExtracted {extracted_count} frames to {OUTPUT_DIR}")
        
        # Copy frames to public folder
        import shutil
        PUBLIC_DIR = '/vercel/share/v0-project/public/frames'
        os.makedirs(PUBLIC_DIR, exist_ok=True)
        for i in range(1, extracted_count + 1):
            src = os.path.join(OUTPUT_DIR, f'frame_{i:04d}.jpg')
            dst = os.path.join(PUBLIC_DIR, f'frame_{i:04d}.jpg')
            if os.path.exists(src):
                shutil.copy2(src, dst)
        print(f"Copied {extracted_count} frames to {PUBLIC_DIR}")
        
        # Clean up temp video
        if os.path.exists(TEMP_VIDEO):
            os.remove(TEMP_VIDEO)
        print("Cleanup complete.")
        
        print(f"\nFrame count for component: {extracted_count}")

    except Exception as error:
        print(f"Error extracting frames: {error}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    extract_frames()
