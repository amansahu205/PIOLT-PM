import { exec } from 'child_process';
import { mkdir } from 'fs/promises';
import { promisify } from 'util';

const execAsync = promisify(exec);

const VIDEO_URL = 'https://hebbkx1anhila5yf.public.blob.vercel-storage.com/Desk_transforming_into_202603290128-irMNNgLKr6LDSWpWAB7imMk9jHUdT5.mp4';
const TEMP_VIDEO = '/tmp/temp_video.mp4';
const OUTPUT_DIR = '/tmp/frames';
const FPS = 30; // Extract 30 frames per second

async function extractFrames() {
  try {
    // Create output directory
    await mkdir(OUTPUT_DIR, { recursive: true });
    console.log(`Created output directory: ${OUTPUT_DIR}`);

    // Download video first
    console.log('Downloading video...');
    await execAsync(`curl -L "${VIDEO_URL}" -o ${TEMP_VIDEO}`);
    console.log('Video downloaded.');

    // Extract frames using ffmpeg
    console.log(`Extracting frames at ${FPS} fps...`);
    await execAsync(`ffmpeg -i ${TEMP_VIDEO} -vf "fps=${FPS}" -q:v 2 ${OUTPUT_DIR}/frame_%04d.jpg`);
    
    // Count frames
    const { stdout } = await execAsync(`ls -1 ${OUTPUT_DIR} | wc -l`);
    const frameCount = parseInt(stdout.trim());
    console.log(`Extracted ${frameCount} frames to ${OUTPUT_DIR}`);

    // Clean up temp video
    await execAsync(`rm ${TEMP_VIDEO}`);
    console.log('Cleanup complete.');

    // Output the frame count for use in the component
    console.log(`\nFrame count for component: ${frameCount}`);
  } catch (error) {
    console.error('Error extracting frames:', error);
  }
}

extractFrames();
