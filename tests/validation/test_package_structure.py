#!/usr/bin/env python3
"""
Package Structure Validation Tests

Tests the overall package structure, imports, and basic functionality
to ensure the narko package is properly structured and installable.
"""

import pytest
import sys
import os
import importlib
import subprocess
from pathlib import Path

# Add src to path for testing
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))


class TestPackageStructure:
    """Test the basic package structure and organization"""
    
    def test_src_directory_exists(self):
        """Test that src directory exists with proper structure"""
        src_dir = project_root / "src" / "narko"
        assert src_dir.exists(), "src/narko directory should exist"
        assert src_dir.is_dir(), "src/narko should be a directory"
    
    def test_required_directories_exist(self):
        """Test that all required package directories exist"""
        required_dirs = [
            "src/narko",
            "src/narko/extensions",
            "src/narko/notion", 
            "src/narko/utils",
            "tests",
            "tests/unit",
            "tests/integration",
            "tests/e2e"
        ]
        
        for dir_path in required_dirs:
            full_path = project_root / dir_path
            assert full_path.exists(), f"Required directory {dir_path} should exist"
            assert full_path.is_dir(), f"{dir_path} should be a directory"
    
    def test_init_files_exist(self):
        """Test that all __init__.py files exist for proper package structure"""
        required_init_files = [
            "src/narko/__init__.py",
            "src/narko/extensions/__init__.py",
            "src/narko/notion/__init__.py",
            "src/narko/utils/__init__.py"
        ]
        
        for init_file in required_init_files:
            full_path = project_root / init_file
            assert full_path.exists(), f"Required __init__.py file {init_file} should exist"
            assert full_path.is_file(), f"{init_file} should be a file"


class TestModuleImports:
    """Test that all modules can be imported correctly"""
    
    def test_main_package_import(self):
        """Test that the main narko package can be imported"""
        try:
            import narko
            assert hasattr(narko, '__version__')
            assert narko.__version__ == "2.0.0"
        except ImportError as e:
            pytest.fail(f"Failed to import narko package: {e}")
    
    def test_core_module_imports(self):
        """Test that core modules can be imported individually"""
        core_modules = [
            'narko.config',
            'narko.converter', 
            'narko.extensions',
            'narko.notion',
            'narko.utils'
        ]
        
        for module_name in core_modules:
            try:
                importlib.import_module(module_name)
            except ImportError as e:
                pytest.fail(f"Failed to import {module_name}: {e}")
    
    def test_extension_imports(self):
        """Test that extension modules can be imported"""
        extension_modules = [
            'narko.extensions.extension',
            'narko.extensions.blocks',
            'narko.extensions.inline'
        ]
        
        for module_name in extension_modules:
            try:
                importlib.import_module(module_name)
            except ImportError as e:
                pytest.fail(f"Failed to import {module_name}: {e}")
    
    def test_notion_module_imports(self):
        """Test that notion modules can be imported"""
        notion_modules = [
            'narko.notion.client',
            'narko.notion.uploader'
        ]
        
        for module_name in notion_modules:
            try:
                importlib.import_module(module_name)
            except ImportError as e:
                pytest.fail(f"Failed to import {module_name}: {e}")
    
    def test_utils_imports(self):
        """Test that utility modules can be imported"""
        util_modules = [
            'narko.utils.cache',
            'narko.utils.validation'
        ]
        
        for module_name in util_modules:
            try:
                importlib.import_module(module_name)
            except ImportError as e:
                pytest.fail(f"Failed to import {module_name}: {e}")
    
    def test_main_class_imports(self):
        """Test that main classes can be imported from package"""
        try:
            from narko import Config, NotionExtension, NotionClient, NotionConverter
            
            # Test that classes exist and are callable
            assert callable(Config)
            assert callable(NotionExtension)
            assert callable(NotionClient)
            assert callable(NotionConverter)
            
        except ImportError as e:
            pytest.fail(f"Failed to import main classes: {e}")


class TestExternalDependencies:
    """Test that external dependencies are available"""
    
    def test_marko_import(self):
        """Test that marko can be imported"""
        try:
            import marko
            from marko.ext import gfm
            assert hasattr(marko, 'Markdown')
        except ImportError as e:
            pytest.fail(f"Failed to import marko: {e}")
    
    def test_requests_import(self):
        """Test that requests can be imported"""
        try:
            import requests
            assert hasattr(requests, 'get')
            assert hasattr(requests, 'post')
        except ImportError as e:
            pytest.fail(f"Failed to import requests: {e}")
    
    def test_dotenv_import(self):
        """Test that python-dotenv can be imported"""
        try:
            from dotenv import load_dotenv
            assert callable(load_dotenv)
        except ImportError as e:
            pytest.fail(f"Failed to import python-dotenv: {e}")
    
    def test_aiohttp_import(self):
        """Test that aiohttp can be imported"""
        try:
            import aiohttp
            assert hasattr(aiohttp, 'ClientSession')
        except ImportError as e:
            pytest.fail(f"Failed to import aiohttp: {e}")
    
    def test_aiofiles_import(self):
        """Test that aiofiles can be imported"""
        try:
            import aiofiles
            assert hasattr(aiofiles, 'open')
        except ImportError as e:
            pytest.fail(f"Failed to import aiofiles: {e}")


class TestCLIFunctionality:
    """Test CLI functionality and help system"""
    
    def test_cli_help_command(self):
        """Test that the CLI displays help correctly"""
        narko_script = project_root / "narko.py"
        
        if not narko_script.exists():
            pytest.skip("Main narko.py script not found")
        
        try:
            result = subprocess.run(
                [sys.executable, str(narko_script), "--help"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            assert result.returncode == 0, f"CLI help command failed: {result.stderr}"
            assert "narko v2.0" in result.stdout, "Help should contain version info"
            assert "Modular Notion extension" in result.stdout, "Help should contain description"
            
        except subprocess.TimeoutExpired:
            pytest.fail("CLI help command timed out")
        except Exception as e:
            pytest.fail(f"CLI help command failed: {e}")
    
    def test_cli_version_info(self):
        """Test that CLI shows version information"""
        narko_script = project_root / "narko.py"
        
        if not narko_script.exists():
            pytest.skip("Main narko.py script not found")
        
        try:
            # Test that script runs without errors when no args provided
            result = subprocess.run(
                [sys.executable, str(narko_script)],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # Should display help and exit cleanly
            assert result.returncode == 0, f"CLI execution failed: {result.stderr}"
            
        except subprocess.TimeoutExpired:
            pytest.fail("CLI execution timed out")
        except Exception as e:
            pytest.fail(f"CLI execution failed: {e}")


class TestConfigurationValidation:
    """Test configuration handling and validation"""
    
    def test_config_class_instantiation(self):
        """Test that Config class can be instantiated"""
        try:
            from narko import Config
            
            # Test with minimal config
            config = Config(
                notion_api_key="test_key",
                notion_import_root="test_root"
            )
            
            assert config.notion_api_key == "test_key"
            assert config.notion_import_root == "test_root"
            
        except Exception as e:
            pytest.fail(f"Config instantiation failed: {e}")
    
    def test_config_validation(self):
        """Test that Config validates required fields"""
        try:
            from narko import Config
            
            # Test that missing required fields raise error
            with pytest.raises(ValueError):
                Config(notion_api_key="", notion_import_root="")
                
        except ImportError as e:
            pytest.fail(f"Failed to import Config: {e}")


class TestBasicFunctionality:
    """Test basic functionality without external dependencies"""
    
    def test_notion_extension_creation(self):
        """Test that NotionExtension can be created"""
        try:
            from narko import NotionExtension
            extension = NotionExtension()
            assert extension is not None
        except Exception as e:
            pytest.fail(f"NotionExtension creation failed: {e}")
    
    def test_converter_instantiation(self):
        """Test that NotionConverter can be instantiated with minimal config"""
        try:
            from narko import Config, NotionConverter
            
            config = Config(
                notion_api_key="test_key",
                notion_import_root="test_root"
            )
            
            # Create with minimal dependencies (will be mocked in real usage)
            converter = NotionConverter(config, None, None)
            assert converter is not None
            
        except Exception as e:
            pytest.fail(f"NotionConverter instantiation failed: {e}")


if __name__ == "__main__":
    # Allow running this test file directly
    pytest.main([__file__, "-v"])