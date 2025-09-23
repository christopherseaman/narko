# Narko Testing Suite

Comprehensive testing framework for the narko file upload and Notion integration system.

## Test Suite Architecture

### Test Categories

- **Unit Tests** (`tests/unit/`) - Fast, isolated tests for individual functions
- **Integration Tests** (`tests/integration/`) - API interaction and service integration tests  
- **End-to-End Tests** (`tests/e2e/`) - Complete workflow validation
- **Performance Tests** (`tests/performance/`) - Speed and resource usage validation
- **Security Tests** (`tests/security/`) - Security vulnerability and attack prevention
- **Load Tests** (`tests/load/`) - High-throughput and concurrent operation testing

### Quick Start

```bash
# Install test dependencies
pip install -r tests/requirements.txt

# Run all tests with coverage
python3 tests/test_runner.py

# Run specific test category
python3 tests/test_runner.py -c unit

# Run quick smoke test
python3 tests/test_runner.py --smoke-test

# Validate test environment
python3 tests/test_runner.py --validate
```

### Test Execution Options

#### By Category
```bash
# Unit tests only (fast)
python3 tests/test_runner.py -c unit

# Integration tests
python3 tests/test_runner.py -c integration

# Performance tests
python3 tests/test_runner.py -c performance

# Security tests
python3 tests/test_runner.py -c security

# Multiple categories
python3 tests/test_runner.py -c unit integration
```

#### Advanced Options
```bash
# Parallel execution
python3 tests/test_runner.py --parallel

# HTML report generation
python3 tests/test_runner.py --html-report

# Benchmark profiling
python3 tests/test_runner.py --benchmark

# Verbose output
python3 tests/test_runner.py --verbose

# Fail fast (stop on first failure)
python3 tests/test_runner.py --fail-fast
```

#### Security and Quality Assurance
```bash
# Run security scans
python3 tests/test_runner.py --security-scan

# Performance profiling
python3 tests/test_runner.py --profile

# Show test summary
python3 tests/test_runner.py --summary
```

### Direct pytest Usage

```bash
# Run specific test file
pytest tests/unit/test_file_processing.py -v

# Run with markers
pytest -m "unit and not slow" -v

# Run with coverage
pytest --cov=narko --cov-report=html

# Run in parallel
pytest -n auto

# Run specific test
pytest tests/unit/test_file_processing.py::TestFileValidation::test_supported_file_types_detection
```

## Test Configuration

### Environment Variables
Set these for testing with real API:
```bash
export NOTION_API_KEY="your_test_api_key"
export NOTION_IMPORT_ROOT="your_test_page_id"
```

### pytest.ini Configuration
The test suite uses pytest markers for categorization:
- `unit`: Fast unit tests
- `integration`: API integration tests
- `e2e`: End-to-end tests
- `performance`: Performance tests
- `security`: Security tests
- `slow`: Long-running tests
- `api`: Tests requiring API access

## Test Coverage Requirements

- **Statements**: >85% (enforced)
- **Branches**: >80% (target)
- **Functions**: >90% (target)
- **Edge Cases**: >75% (target)

## Performance Benchmarks

### Target Performance Metrics
- File upload processing: <100ms for files under 1MB
- Markdown processing: <500ms for documents with <100 blocks
- Memory usage: <50MB increase per file processed
- API response handling: <2s timeout for file uploads
- Large file processing: <5s for files up to 5MB limit

### Load Testing Scenarios  
- Concurrent upload handling: 10+ simultaneous uploads
- Large document processing: 1000+ block documents
- Memory leak detection: 100+ file processing cycles
- Cache performance: 90%+ cache hit rate validation
- API rate limiting: Graceful degradation under limits

## Security Testing

### Security Test Categories
1. **Input Validation**
   - File type validation bypass attempts
   - Path traversal prevention
   - Filename sanitization
   - File size limit enforcement

2. **API Security**
   - Authentication token validation
   - API key exposure prevention
   - Request/response sanitization
   - Rate limiting respect

3. **File System Security**
   - Temporary file cleanup
   - Permission validation
   - Symlink attack prevention
   - Directory traversal protection

4. **Content Security**
   - Malicious file content handling
   - Script injection prevention
   - XSS prevention in generated content
   - Binary file validation

## Test Data and Fixtures

### Fixture Categories
- Sample files (images, documents, code files)
- API response mocks
- Test configurations
- Performance test data
- Security test payloads

### Shared Fixtures (conftest.py)
- `temp_dir`: Temporary directory for test files
- `mock_notion_api`: Mocked Notion API responses
- `sample_image_file`: Minimal PNG for testing
- `sample_text_file`: Text file for testing
- `large_file`: 4MB file for performance testing
- `oversized_file`: 6MB file for limit testing
- `mock_env_vars`: Test environment variables

## Continuous Integration

### GitHub Actions Integration
```yaml
- name: Run Test Suite
  run: |
    pip install -r tests/requirements.txt
    python3 tests/test_runner.py --parallel --html-report

- name: Security Scan
  run: python3 tests/test_runner.py --security-scan

- name: Upload Coverage
  uses: codecov/codecov-action@v3
```

### Quality Gates
- All tests must pass
- Coverage must be >85%
- No security vulnerabilities
- Performance benchmarks must pass
- Memory usage within limits

## Debugging Tests

### Common Issues
1. **Import Errors**: Ensure `narko.py` is in Python path
2. **API Key Issues**: Check environment variables for integration tests
3. **File Permission Issues**: Ensure test files are writable
4. **Network Issues**: Mock external API calls for unit tests

### Debug Commands
```bash
# Run with debug output
pytest -s -vv tests/unit/test_file_processing.py

# Run single test with pdb
pytest --pdb tests/unit/test_file_processing.py::test_function

# Profile memory usage
pytest --memray tests/performance/

# Check test collection
pytest --collect-only tests/
```

## Contributing to Tests

### Adding New Tests
1. Follow naming convention: `test_*.py`
2. Use appropriate markers: `@pytest.mark.unit`, etc.
3. Include docstrings describing test purpose
4. Mock external dependencies
5. Use fixture data when possible

### Test Code Style
- Use descriptive test names
- Follow Arrange-Act-Assert pattern
- One assertion per test (when possible)
- Use fixtures for test data
- Mock external dependencies
- Handle edge cases explicitly

### Performance Test Guidelines
- Use `benchmark` fixture for timing
- Set reasonable performance targets
- Test both best and worst case scenarios
- Monitor memory usage
- Test concurrent operations

### Security Test Guidelines  
- Test all input validation points
- Verify error handling
- Check for information leakage
- Test boundary conditions
- Validate security headers/responses

## Reporting Issues

When reporting test failures:
1. Include full error output
2. Specify test category and file
3. Include environment details
4. Attach relevant log files
5. Describe expected vs actual behavior

## Test Metrics Dashboard

The test suite generates several reports:
- **Coverage Report**: `htmlcov/index.html`
- **Test Report**: `test_report.html` 
- **Benchmark Results**: `benchmark_results.json`
- **Security Report**: `security_report.json`
- **JUnit XML**: `test-results.xml`

These reports provide detailed insights into test execution, performance, and code quality.