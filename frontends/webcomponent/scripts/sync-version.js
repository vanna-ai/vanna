/**
 * Sync version from pyproject.toml to package.json
 *
 * This ensures the webcomponent version always matches the Python package version.
 * Single source of truth: pyproject.toml
 *
 * Usage: node scripts/sync-version.js
 */

const fs = require('fs');
const path = require('path');

// Paths relative to this script
const PYPROJECT_PATH = path.join(__dirname, '../../../pyproject.toml');
const PACKAGE_JSON_PATH = path.join(__dirname, '../package.json');

function extractVersionFromPyproject(content) {
  // Match: version = "2.0.0"
  const match = content.match(/^version\s*=\s*"([^"]+)"/m);
  if (!match) {
    throw new Error('Could not find version in pyproject.toml');
  }
  return match[1];
}

function updatePackageJsonVersion(packageJsonPath, newVersion) {
  const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
  const oldVersion = packageJson.version;

  packageJson.version = newVersion;

  fs.writeFileSync(
    packageJsonPath,
    JSON.stringify(packageJson, null, 2) + '\n',
    'utf8'
  );

  return { oldVersion, newVersion };
}

function main() {
  try {
    // Read pyproject.toml
    const pyprojectContent = fs.readFileSync(PYPROJECT_PATH, 'utf8');
    const version = extractVersionFromPyproject(pyprojectContent);

    // Update package.json
    const { oldVersion, newVersion } = updatePackageJsonVersion(PACKAGE_JSON_PATH, version);

    if (oldVersion !== newVersion) {
      console.log(`✓ Version synced: ${oldVersion} → ${newVersion}`);
    } else {
      console.log(`✓ Version already in sync: ${newVersion}`);
    }

    process.exit(0);
  } catch (error) {
    console.error(`✗ Version sync failed: ${error.message}`);
    process.exit(1);
  }
}

main();
