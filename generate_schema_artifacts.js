#!/usr/bin/env node

/**
 * CLI entrypoint for schema artifact generation.
 * Pure logic lives in schemaArtifactsCore.js and schemaArtifactsCli.js.
 * This file is just a thin wrapper that delegates to the CLI module.
 */

const cli = require('./schemaArtifactsCli');

if (require.main === module) {
  cli.runCli(process.argv);
}

// Re-export core and CLI for programmatic use
const core = require('./schemaArtifactsCore');
module.exports = {
  ...core,
  ...cli
};

