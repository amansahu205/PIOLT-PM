import { cp } from 'fs/promises';

async function copyFrames() {
  try {
    console.log('Copying frames from /tmp/frames/ to /vercel/share/v0-project/public/frames/...');
    await cp('/tmp/frames', '/vercel/share/v0-project/public/frames', { recursive: true });
    console.log('Frames copied successfully!');
  } catch (error) {
    console.error('Error copying frames:', error.message);
  }
}

copyFrames();
