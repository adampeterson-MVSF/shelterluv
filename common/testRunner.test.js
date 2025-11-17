/**
 * Tests for the refactored testRunner module.
 * Tests integration of command builder, runner, and artifact writer.
 */

const { runAllTests, writeTestArtifacts } = require('./testRunner');

describe('testRunner integration', () => {
  test('exports expected functions', () => {
    expect(typeof runAllTests).toBe('function');
    expect(typeof writeTestArtifacts).toBe('function');
  });

  test('runAllTests returns expected structure', async () => {
    // Mock execSync to avoid actually running tests
    const originalExecSync = require('child_process').execSync;
    require('child_process').execSync = jest.fn(() => 'mock test output');

    try {
      const results = await runAllTests({ continueOnError: true, log: () => {} });

      expect(results).toHaveProperty('timestamp');
      expect(results).toHaveProperty('webapp');
      expect(results).toHaveProperty('etl');
      expect(results).toHaveProperty('e2e');

      expect(results.webapp).toHaveProperty('service', 'webapp');
      expect(results.etl).toHaveProperty('service', 'etl');
      expect(results.e2e).toHaveProperty('service', 'webapp-e2e');
    } finally {
      // Restore original function
      require('child_process').execSync = originalExecSync;
    }
  });

  test('writeTestArtifacts handles missing artifacts directory', () => {
    const mockResults = {
      timestamp: '2024-01-01T00:00:00.000Z',
      webapp: { success: true, stdout: 'webapp output', stderr: '', exitCode: 0 },
      etl: { success: true, stdout: 'etl output', stderr: '', exitCode: 0 },
      e2e: { success: false, stdout: 'e2e output', stderr: '', exitCode: 1 }
    };

    let artifactsDirCreated = false;
    let jsonFileWritten = false;
    let txtFileWritten = false;

    const mockWriteFile = (path, content) => {
      if (path === 'artifacts/test-results.json') {
        jsonFileWritten = true;
        expect(JSON.parse(content)).toEqual(mockResults);
      } else if (path === 'artifacts/TESTS.txt') {
        txtFileWritten = true;
        expect(content).toContain('REACT WEBAPP TESTS');
        expect(content).toContain('SOME FAILED');
      }
    };

    const mockMkdir = (path) => {
      if (path === 'artifacts') {
        artifactsDirCreated = true;
      }
    };

    const mockExists = (path) => path !== 'artifacts'; // Pretend artifacts doesn't exist

    writeTestArtifacts(mockResults, {
      writeFile: mockWriteFile,
      mkdir: mockMkdir,
      exists: mockExists
    });

    expect(artifactsDirCreated).toBe(true);
    expect(jsonFileWritten).toBe(true);
    expect(txtFileWritten).toBe(true);
  });
});
