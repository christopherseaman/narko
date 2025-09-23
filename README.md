# narko

**Notion extension and uploader for marko** - A clean, extension-based markdown to Notion converter using proper marko extensions.

## Features

- ✅ **Proper marko extensions** - No hacky post-processing, follows official marko API
- ✅ **Full markdown support** - Code blocks, tables, lists, links, formatting
- ✅ **Extended syntax** - Task lists, math equations, callouts, highlights
- ✅ **Language detection** - 80+ programming languages with syntax highlighting
- ✅ **Obsidian compatibility** - Handles wiki links, tags, callouts, frontmatter
- ✅ **Text chunking** - Respects Notion's 2000-character limits
- ✅ **Python package** - Clean package structure with CLI interface

## Quick Start

```bash
# Install (development mode)
pip install -e .

# Test conversion
narko --file README.md --test

# Import to Notion
narko --file README.md --import
```

## Supported Extensions

| Extension | Syntax | Notion Block |
|-----------|--------|--------------|
| **Task Lists** | `- [x] Done`<br>`- [ ] Todo` | To-do blocks |
| **Math Blocks** | `$$E = mc^2$$` | Equation blocks |
| **Inline Math** | `$E = mc^2$` | Code formatting |
| **Highlights** | `==highlighted==` | Yellow background |
| **Callouts** | `> [!NOTE]`<br>`> Content` | Callout blocks |

## Supported Languages

Supports 80+ programming languages including:

**Popular:** Python, JavaScript, TypeScript, Java, C/C++, Rust, Go, Swift, Kotlin  
**Web:** HTML, CSS, SCSS, GraphQL, JSON, YAML  
**Data:** SQL, TOML, Protobuf, YAML  
**Specialized:** Mermaid, LaTeX, Docker, Makefile, Solidity  
**Functional:** Haskell, Elixir, F#, Clojure, Erlang

Plus common aliases: `py→python`, `js→javascript`, `ts→typescript`, `dockerfile→docker`

## Setup

1. **Install Package**:
   ```bash
   git clone <repository-url>
   cd narko
   pip install -e .
   ```

2. **Environment Variables**:
   ```bash
   export NOTION_API_KEY="your_integration_token_here"
   export NOTION_IMPORT_ROOT="your_parent_page_id_here"
   ```

3. **Notion Integration**:
   - Create integration at [developers.notion.com](https://developers.notion.com)
   - Create/share a parent page in Notion with the integration
   - Use the page ID from the URL as your `NOTION_IMPORT_ROOT`

## Usage

```bash
# Test mode - shows blocks without importing
narko --file document.md --test

# Import to Notion
narko --file document.md --import

# Import to specific parent page
narko --file document.md --parent your_page_id --import

# Replace modes (advanced)
narko --file document.md --replace-all --import        # Replace all content
narko --file document.md --replace-content --import    # Replace content, keep sub-pages
```

## Architecture

**Marko Extensions:**
- `MathBlock` - Parses `$$...$$` blocks
- `TaskListItem` - Parses `- [x]` checkboxes  
- `Highlight` - Parses `==text==` highlighting
- `InlineMath` - Parses `$...$` inline math
- `CalloutBlock` - Parses `> [!TYPE]` callouts

**Notion Converter:**
- AST-based processing with proper marko extension API
- Text chunking for 2000-character limit compliance
- Language mapping for 80+ programming languages
- Obsidian syntax cleaning (wiki links, tags, frontmatter)

## 🪔 Wishlist (wishful thinking to-do list)

### 🏗️ **Architecture & Distribution**
- ✅ Split into proper Python package structure (`narko/`, `setup.py`, etc.)
- Publish to PyPI as `pip install narko`
- Separate marko extensions into standalone package for reuse

### 🧪 **Quality & Testing**
- ✅ Add comprehensive test suite with pytest
- Create GitHub Actions workflow for CI/CD  
- Add verbose/debug logging modes
- Improve test organization and coverage

### ✨ **Features**
- Table support verification (marko[gfm] integration)
- ✅ Image/file upload handling for embedded content
- Batch processing for multiple files at once
- Nested page creation from directory structure
- Strikethrough annotation support (`~~text~~`)
- **API Coverage Expansion** - Currently ~85-90% coverage for markdown import:
  - Missing: underline formatting, extended color palette
  - Page property updates (title, metadata modification)  
  - Database integration (create pages in databases)
  - Search API integration for existing page discovery
  - *See `tmp_docs/notion_api_docs/` and `tmp_docs/formatting_coverage_analysis.md` for detailed analysis*

### 🔧 **UX Improvements**
- ✅ Configuration file support (vs hardcoded page map)
- ✅ CLI option to specify parent page directly (--parent)
- ✅ Remove dependency on page_map.json file
- Incremental updates (only process changed files)
- Better error handling and user feedback