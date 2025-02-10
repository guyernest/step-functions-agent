#!/bin/bash

# Clean up any existing files
rm -rf dist/
rm -rf layers/chromium/nodejs
rm -f layers/chromium/chromium.zip

# Install project dependencies and build TypeScript
echo "Installing project dependencies..."
npm install
npm run build

# Copy package.json and install production dependencies in dist
echo "Setting up production dependencies..."
cp package.json dist/
cd dist
npm install --production
rm package.json package-lock.json
cd ..

# Create the layer
echo "Creating Chromium layer..."
mkdir -p layers/chromium/nodejs

# Install Chromium in the layer with the correct architecture
cd layers/chromium/nodejs
npm init -y

# Install the chromium package specifically for ARM64
echo "Installing Chromium for ARM64..."
cat > package.json << EOL
{
  "name": "chromium-layer",
  "version": "1.0.0",
  "dependencies": {
    "@sparticuz/chromium": "132.0.0"
  }
}
EOL

# Install dependencies with architecture-specific flags
# Sadly, this doesn't work because the chromium package is not available for ARM64
npm install --arch=arm64 --platform=linux

# Create the zip file with debug information
cd ..
echo "Creating layer zip file..."
echo "Contents of nodejs/node_modules/@sparticuz/chromium/bin:"
ls -la nodejs/node_modules/@sparticuz/chromium/bin
echo "File type of chromium binary:"
file nodejs/node_modules/@sparticuz/chromium/bin/*

# Create the zip file
zip -r chromium.zip nodejs/

echo "Layer has been created at layers/chromium/chromium.zip"
cd ../..