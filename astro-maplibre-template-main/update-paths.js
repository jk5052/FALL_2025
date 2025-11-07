import { readFileSync, writeFileSync, readdirSync, statSync } from "fs";
import { join } from "path";

async function getConfigBasePath() {
    const astroConfig = await import("./astro.config.mjs"); // Dynamically import config
    const basePath = astroConfig.default.base;
    const site = astroConfig.default.site;
    return `${site}/${basePath}`;
}

const __dirname = new URL(".", import.meta.url).pathname;

async function updatePaths(basePath) {
    const distDir = join(__dirname, "dist");

    function updateFilePaths(filePath) {
        let content = readFileSync(filePath, "utf8");

        // Update href and src attributes for base path
        content = content.replace(/href="\.\//g, `href="${basePath}/`)
                         .replace(/src="\.\//g, `src="${basePath}/`);

        // Regex for matching data-layers and data-mapstyle attributes
        const dataLayersRegex = /data-layers="([^"]*)"/g;
        const dataMapstyleRegex = /data-mapstyle="([^"]*)"/g;
        const dataBlockRegex = /<inline-mixed-content[^>]*data-block="([^"]*)"/g;
        const imgTagRegex = /<img\s+[^>]*src="([^"]+)"[^>]*>/g;

        // Update data-layers JSON URLs
        content = content.replace(dataLayersRegex, (match, jsonStr) => {
            try {
                const decodedLayers = JSON.parse(
                    jsonStr.replace(/&quot;/g, "\"").replace(/&#34;/g, "\"")
                );

                const updatedLayers = decodedLayers.map(layer => {
                    if (layer.url && layer.url.startsWith("./")) {
                        layer.url = `${basePath}${layer.url.slice(1)}`;
                    }
                    return layer;
                });

                const encodedLayers = JSON.stringify(updatedLayers).replace(/"/g, "&quot;");
                return `data-layers="${encodedLayers}"`;
            } catch (error) {
                console.error(`Failed to parse data-layers JSON in file ${filePath}:`, error);
                return match; // Return original if parsing fails
            }
        });

        // Update data-mapstyle if it contains a relative URL
        content = content.replace(dataMapstyleRegex, (match, urlStr) => {
            if (urlStr.startsWith("./")) {
                const updatedUrl = `${basePath}${urlStr.slice(1)}`;
                return `data-mapstyle="${updatedUrl}"`;
            }
            return match; // Return original if not a relative path
        });

        // Update image `src` paths within inline-mixed-content data-block attributes
        content = content.replace(dataBlockRegex, (match, jsonStr) => {
            try {
                const decodedBlock = JSON.parse(
                    jsonStr.replace(/&quot;/g, "\"").replace(/&#34;/g, "\"")
                );

                const updatedBlock = decodedBlock.map((block) => {
                    if (block.img) {
                        block.img = block.img.map((img) => {
                            if (img.src && img.src.startsWith("./")) {
                                img.src = `${basePath}${img.src.slice(1)}`;
                            }
                            return img;
                        });
                    }
                    return block;
                });

                const encodedBlock = JSON.stringify(updatedBlock).replace(/"/g, "&quot;");
                return match.replace(jsonStr, encodedBlock);
            } catch (error) {
                console.error(`Failed to parse data-block JSON in file ${filePath}:`, error);
                return match; // Return original if parsing fails
            }
        });

        // Update plain <img> tags with relative `src` attributes
        content = content.replace(imgTagRegex, (match, src) => {
            if (src.startsWith("./")) {
                const updatedSrc = `${basePath}${src.slice(1)}`;
                return match.replace(src, updatedSrc);
            }
            return match; // Return original if not a relative path
        });

        writeFileSync(filePath, content, "utf8");
    }

    function processDirectory(dir) {
        readdirSync(dir).forEach((file) => {
            const filePath = join(dir, file);
            if (statSync(filePath).isDirectory()) {
                processDirectory(filePath);
            } else if (file.endsWith(".html")) {
                updateFilePaths(filePath);
            }
        });
    }

    processDirectory(distDir);
}

// Run the script with the base path from astro.config.mjs
getConfigBasePath().then((basePath) => {
    console.log(`Using base path: ${basePath}`);
    updatePaths(basePath);
}).catch((err) => {
    console.error("Error reading base path from astro.config.mjs:", err);
});
