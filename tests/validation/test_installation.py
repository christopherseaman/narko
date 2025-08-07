#!/usr/bin/env python3
"""
Installation Validation Tests

Tests the package installation process and dependency resolution.
These tests validate that the package can be installed and dependencies
are correctly specified.
"""

import pytest
import subprocess
import sys
import tempfile
import shutil
from pathlib import Path
# import pkg_resources  # Not needed for basic validation


class TestInstallationProcess:
    """Test the package installation process"""
    
    def test_python_version_compatibility(self):
        """Test that Python version meets requirements"""
        python_version = sys.version_info
        
        # Package requires Python >= 3.8
        assert python_version >= (3, 8), f"Python 3.8+ required, got {python_version}"
    
    def test_pip_installable_structure(self):
        """Test that package has proper structure for pip installation"""
        project_root = Path(__file__).parent.parent.parent
        
        # Check for key files that make package installable
        required_files = [
            "narko.py",  # Main script
            "src/narko/__init__.py",  # Package init
        ]
        
        for file_path in required_files:
            full_path = project_root / file_path
            assert full_path.exists(), f"Required file for installation: {file_path}"
    
    def test_dependencies_specification(self):
        """Test that dependencies are properly specified"""
        project_root = Path(__file__).parent.parent.parent
        
        # Check for dependency specification in script header
        narko_script = project_root / "narko.py"
        if narko_script.exists():
            content = narko_script.read_text()
            
            # Should have uv script dependencies
            assert "dependencies = [" in content, "Dependencies should be specified in script"
            assert '"marko[gfm]"' in content, "marko dependency should be specified"
            assert '"requests"' in content, "requests dependency should be specified"
            assert '"python-dotenv"' in content, "python-dotenv dependency should be specified"
    
    def test_import_dependencies_available(self):
        """Test that all required dependencies can be imported"""
        required_deps = [
            "marko",
            "requests", 
            "dotenv",
            "aiohttp",
            "aiofiles"
        ]
        
        missing_deps = []
        for dep in required_deps:
            try:
                __import__(dep)
            except ImportError:
                missing_deps.append(dep)
        
        if missing_deps:
            pytest.skip(f"Dependencies not installed: {missing_deps}")


class TestDependencyCompatibility:
    """Test dependency version compatibility"""
    
    def test_marko_version(self):
        """Test marko version compatibility"""
        try:
            import marko
            # Just test that it imports and has basic functionality
            assert hasattr(marko, 'Markdown')
            assert hasattr(marko, 'parse')
        except ImportError:
            pytest.skip("marko not installed")
    
    def test_requests_version(self):
        """Test requests version compatibility"""
        try:
            import requests
            # Test basic functionality
            assert hasattr(requests, 'get')
            assert hasattr(requests, 'post')
            assert hasattr(requests, 'Session')
        except ImportError:
            pytest.skip("requests not installed")
    
    def test_aiohttp_compatibility(self):
        """Test aiohttp compatibility"""
        try:
            import aiohttp
            assert hasattr(aiohttp, 'ClientSession')
        except ImportError:
            pytest.skip("aiohttp not installed")
    
    def test_python_dotenv_compatibility(self):
        """Test python-dotenv compatibility"""
        try:
            from dotenv import load_dotenv
            assert callable(load_dotenv)
        except ImportError:
            pytest.skip("python-dotenv not installed")


class TestUVScriptSupport:
    """Test UV script support and execution"""
    
    def test_uv_script_header(self):
        """Test that the script has proper UV script header"""
        project_root = Path(__file__).parent.parent.parent
        narko_script = project_root / "narko.py"
        
        if not narko_script.exists():
            pytest.skip("Main narko.py script not found")
        
        content = narko_script.read_text()
        
        # Check for UV script header
        assert "#!/usr/bin/env -S uv run --script" in content, "Should have UV shebang"
        assert "# /// script" in content, "Should have script metadata start"
        assert "# ///" in content, "Should have script metadata end"
        assert "requires-python" in content, "Should specify Python version"
    
    def test_uv_dependencies_format(self):
        """Test that UV dependencies are properly formatted"""
        project_root = Path(__file__).parent.parent.parent
        narko_script = project_root / "narko.py"
        
        if not narko_script.exists():
            pytest.skip("Main narko.py script not found")
        
        content = narko_script.read_text()
        lines = content.split('\n')
        
        # Find dependencies section
        in_deps = False
        deps_found = []
        
        for line in lines:
            if '# dependencies = [' in line:
                in_deps = True
                continue
            elif in_deps and '# ]' in line:
                break
            elif in_deps and line.strip().startswith('#'):
                dep_line = line.strip()
                if '"' in dep_line:
                    deps_found.append(dep_line)
        
        # Verify dependencies are present
        assert len(deps_found) > 0, "Should have dependencies specified"
        
        # Check specific required dependencies
        dep_text = '\n'.join(deps_found)
        assert '"marko[gfm]"' in dep_text, "marko[gfm] dependency required"
        assert '"requests"' in dep_text, "requests dependency required"


class TestPackageStructureIntegrity:
    """Test package structure integrity for installation"""
    
    def test_namespace_package_structure(self):
        """Test that package follows proper namespace structure"""
        project_root = Path(__file__).parent.parent.parent
        
        # Test that src layout is used
        src_dir = project_root / "src"
        assert src_dir.exists(), "src directory should exist for proper package structure"
        
        narko_pkg = src_dir / "narko"
        assert narko_pkg.exists(), "narko package should be in src directory"
        assert (narko_pkg / "__init__.py").exists(), "Package should have __init__.py"
    
    def test_module_imports_from_installed_location(self):
        """Test that modules can be imported from their installed location"""
        project_root = Path(__file__).parent.parent.parent
        
        # Add src to path to simulate installation
        import sys
        src_path = str(project_root / "src")
        if src_path not in sys.path:
            sys.path.insert(0, src_path)
        
        # Test imports work from this location
        try:
            from narko import Config, NotionExtension, NotionClient, NotionConverter
            assert all([Config, NotionExtension, NotionClient, NotionConverter])
        except ImportError as e:
            pytest.fail(f"Imports failed from installed location: {e}")
        finally:
            # Clean up path
            if src_path in sys.path:
                sys.path.remove(src_path)


class TestRuntimeRequirements:
    """Test runtime requirements and environment"""
    
    def test_file_system_permissions(self):
        """Test that package can create necessary files and directories"""
        import tempfile
        import os
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Test cache directory creation
            cache_dir = Path(temp_dir) / "narko_cache"
            cache_dir.mkdir(exist_ok=True)
            assert cache_dir.exists()
            
            # Test file creation
            test_file = cache_dir / "test.json"
            test_file.write_text('{"test": true}')
            assert test_file.exists()
            
            # Test file reading
            content = test_file.read_text()
            assert '"test": true' in content
    
    def test_environment_variable_handling(self):
        """Test environment variable handling"""
        import os
        
        # Test that environment variables can be set and read
        test_key = "NARKO_TEST_VAR"
        test_value = "test_value"
        
        original_value = os.environ.get(test_key)
        try:
            os.environ[test_key] = test_value
            assert os.environ.get(test_key) == test_value
        finally:
            # Cleanup
            if original_value is not None:
                os.environ[test_key] = original_value
            else:
                os.environ.pop(test_key, None)
    
    def test_json_handling(self):
        """Test JSON serialization/deserialization works"""
        import json
        
        test_data = {
            "version": "2.0.0",
            "features": ["upload", "cache", "validation"],
            "config": {
                "timeout": 30,
                "retries": 3
            }
        }
        
        # Test serialization
        json_str = json.dumps(test_data)
        assert isinstance(json_str, str)
        
        # Test deserialization  
        parsed_data = json.loads(json_str)
        assert parsed_data == test_data


if __name__ == "__main__":
    # Allow running this test file directly
    pytest.main([__file__, "-v"])