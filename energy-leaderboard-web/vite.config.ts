import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import fs from 'fs'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
    plugins: [
        react(),
        {
            name: 'generate-data-manifest',
            configureServer(server) {
                const dataDir = path.resolve(__dirname, 'public/data');
                const manifestPath = path.join(dataDir, 'manifest.json');

                function updateManifest() {
                    try {
                        if (!fs.existsSync(dataDir)) return;

                        const files = fs.readdirSync(dataDir)
                            .filter((file: string) => file.endsWith('.json') && file !== 'manifest.json');

                        fs.writeFileSync(manifestPath, JSON.stringify(files, null, 2));
                        console.log(`[manifest] Updated with ${files.length} files`);
                    } catch (err) {
                        console.error('[manifest] Error updating manifest:', err);
                    }
                }

                // Initial generation
                updateManifest();

                // Watch for changes
                server.watcher.add(dataDir);
                server.watcher.on('add', (filePath) => {
                    if (filePath.includes('public/data') && filePath.endsWith('.json')) updateManifest();
                });
                server.watcher.on('unlink', (filePath) => {
                    if (filePath.includes('public/data') && filePath.endsWith('.json')) updateManifest();
                });
            },
            buildStart() {
                const dataDir = path.resolve(__dirname, 'public/data');
                const manifestPath = path.join(dataDir, 'manifest.json');

                try {
                    if (!fs.existsSync(dataDir)) return;

                    const files = fs.readdirSync(dataDir)
                        .filter((file: string) => file.endsWith('.json') && file !== 'manifest.json');

                    fs.writeFileSync(manifestPath, JSON.stringify(files, null, 2));
                    console.log(`[manifest] Generated for build with ${files.length} files`);
                } catch (err) {
                    console.error('[manifest] Error generating manifest:', err);
                }
            }
        }
    ],
    // For GitHub Pages: set base to repo name (update if your repo name differs)
    base: '/energy-leaderboard-runner/',
    build: {
        outDir: 'dist',
    },
})
