# narko

**Notion extension and uploader for marko** - A clean, extension-based markdown to Notion converter using proper marko extensions.

## Features

- ✅ **Proper marko extensions** - No hacky post-processing, follows official marko API
- ✅ **Full markdown support** - Code blocks, tables, lists, links, formatting
- ✅ **Extended syntax** - Task lists, math equations, callouts, highlights
- ✅ **Language detection** - 80+ programming languages with syntax highlighting
- ✅ **Obsidian compatibility** - Handles wiki links, tags, callouts, frontmatter
- ✅ **Text chunking** - Respects Notion's 2000-character limits
- ✅ **Zero dependencies** - Self-contained uv script

## Quick Start

```bash
# Test conversion
uv run narko.py --file README.md --test

# Import to Notion
uv run narko.py --file README.md --import
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

1. **Environment Variables** - Copy and configure:
   ```bash
   cp .env.example .env
   # Edit .env with your Notion integration token
   ```
   ```
   NOTION_API_KEY=your_integration_token_here
   ```

2. **Page Mapping** - Copy and configure:
   ```bash
   cp page_map.json.example page_map.json
   # Edit page_map.json with your parent page ID
   ```
   ```json
   {
     ".": "your_parent_page_id_here"
   }
   ```

3. **Notion Integration**:
   - Create integration at [developers.notion.com](https://developers.notion.com)
   - Copy the integration token to `.env`
   - Create/share a parent page in Notion with the integration
   - Copy the page ID from the URL to `page_map.json`

## Usage

```bash
# Test mode - shows blocks without importing
uv run narko.py --file document.md --test

# Import to Notion
uv run narko.py --file document.md --import

# Process specific file
uv run narko.py --file path/to/markdown.md --import
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

## License

MIT