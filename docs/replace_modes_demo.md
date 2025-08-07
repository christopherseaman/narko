# Replace Modes Implementation Summary

## 🎯 New Features Added

We've successfully implemented **two new replace modes** for the Notion integration:

### 1. **Replace All Mode** (`--replace-all`)
- **Purpose**: Replace ALL content on a page, including sub-pages
- **Use Case**: Complete page overhaul
- **Behavior**: Deletes everything and replaces with new content

### 2. **Replace Content Mode** (`--replace-content`)  
- **Purpose**: Replace content blocks but preserve sub-pages
- **Use Case**: Update content while keeping sub-page structure
- **Behavior**: Deletes only content blocks, preserves child_page blocks

## 📋 All Available Modes

| Mode | Flag | Behavior |
|------|------|----------|
| **Create** | (default) | Creates new sub-page under parent |
| **Append** | `--append` | Adds content to end of existing page |
| **Replace All** | `--replace-all` | Replaces ALL content (including sub-pages) |
| **Replace Content** | `--replace-content` | Replaces content but preserves sub-pages |

## 🔧 Implementation Details

### New Methods Added to `NotionClient`:

1. **`get_page_blocks(page_id)`**
   - Retrieves all blocks from a page recursively
   - Handles pagination automatically
   - Returns list of block objects

2. **`delete_blocks(block_ids)`**
   - Deletes multiple blocks efficiently
   - Returns success/error counts
   - Handles partial failures gracefully

3. **`replace_all_blocks(page_id, new_blocks)`**
   - Gets existing blocks → deletes all → adds new blocks
   - Returns detailed operation statistics
   - Atomic-like operation with error handling

4. **`replace_content_blocks(page_id, new_blocks)`** 
   - Gets existing blocks → identifies content vs sub-pages
   - Deletes only content blocks → adds new blocks
   - Preserves sub-page structure

### Enhanced Main Application:

- **Updated `import_to_notion()`** method signature:
  - Changed from `append_mode: bool` to `mode: str`
  - Supports all four modes: 'create', 'append', 'replace_all', 'replace_content'

- **Enhanced CLI Arguments**:
  - Added mutually exclusive argument group
  - Clear help text for each mode
  - Updated examples in help output

## 🧪 Testing

Comprehensive test suite added in `tests/test_replace_modes.py`:

- ✅ Block retrieval functionality
- ✅ Block deletion with error handling  
- ✅ Replace all blocks end-to-end
- ✅ Replace content blocks with sub-page preservation
- ✅ CLI integration verification

All tests passing: **6/6** ✅

## 📖 Usage Examples

```bash
# Create new sub-page (default)
python run_narko.py --file document.md --import

# Append to existing page  
python run_narko.py --file document.md --import --append

# Replace ALL content (including sub-pages)
python run_narko.py --file document.md --import --replace-all

# Replace content but keep sub-pages
python run_narko.py --file document.md --import --replace-content
```

## 📊 Success Metrics

When operations complete, users see detailed feedback:

**Replace All Example:**
```
✅ Successfully replaced all content: https://www.notion.so/page-id
   🗑️  Deleted 15 blocks, ➕ Added 8 blocks
```

**Replace Content Example:**  
```
✅ Successfully replaced content: https://www.notion.so/page-id
   🗑️  Deleted 12 content blocks, 📄 Preserved 3 sub-pages, ➕ Added 8 blocks
```

## 🔒 Safety Features

- **Validation**: All blocks validated before operations
- **Error Handling**: Graceful handling of API failures
- **Atomic-like Operations**: Complete success or clear error reporting
- **Detailed Logging**: Operation statistics for transparency
- **Block Limits**: Respects Notion's 100-block limit per request

## ✨ Key Benefits

1. **Flexibility**: Four distinct modes for different use cases
2. **Safety**: Content preservation options for sub-pages
3. **Transparency**: Clear feedback on what was changed
4. **Robustness**: Comprehensive error handling
5. **Performance**: Efficient bulk operations

The implementation provides powerful new ways to manage Notion content while maintaining the existing functionality and ensuring backward compatibility.