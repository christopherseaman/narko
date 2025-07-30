# Comprehensive Test Suite for narko

This document tests all CommonMark features plus Notion-specific extensions supported by narko.

---

## 1. Headers

# Heading 1
## Heading 2  
### Heading 3
#### Heading 4 (becomes H3 in Notion)
##### Heading 5 (becomes H3 in Notion)
###### Heading 6 (becomes H3 in Notion)

---

## 2. Text Formatting

**Bold text** and *italic text* and ***bold italic text***

~~Strikethrough text~~ (not supported in Notion API)

`Inline code` formatting

---

## 3. Lists

### Unordered Lists
- Item 1
- Item 2
  - Nested item 2.1
  - Nested item 2.2
- Item 3

### Ordered Lists
1. First item
2. Second item
   1. Nested numbered item
   2. Another nested item
3. Third item

---

## 4. Task Lists (narko extension)
- [x] Completed task
- [ ] Uncompleted task
- [X] Another completed task
- [ ] Another uncompleted task

---

## 5. Links and References

[Link to Google](https://google.com)

[Link with title](https://github.com "GitHub Homepage")

Autolink: https://example.com

---

## 6. Code Blocks

```python
def hello_world():
    print("Hello, World!")
    return True
```

```javascript
const greeting = "Hello";
console.log(greeting + " World!");
```

```sql
SELECT name, age 
FROM users 
WHERE active = true;
```

```
Plain text code block
with multiple lines
```

---

## 7. Math (narko extensions)

### Block Math
$$
E = mc^2
$$

$$
\sum_{i=1}^{n} x_i = x_1 + x_2 + \cdots + x_n
$$

### Inline Math
The equation $E = mc^2$ is famous, and so is $\pi \approx 3.14159$.

---

## 8. Highlights (narko extension)

This is ==highlighted text== in yellow background.

You can have ==multiple highlighted== sections in ==one paragraph==.

---

## 9. Callouts (narko extension)

> [!NOTE]
> This is a note callout with important information.

> [!TIP]
> This is a tip callout with helpful advice.

> [!WARNING]
> This is a warning callout about potential issues.

> [!DANGER]
> This is a danger callout about critical issues.

> [!INFO]
> This is an info callout with general information.

> [!IMPORTANT]
> This is an important callout that stands out.

> [!EXAMPLE]
> This is an example callout showing how something works.

---

## 10. Blockquotes

> This is a regular blockquote
> that spans multiple lines
> and shows quoted content.

> Nested blockquotes
>> are also supported
>>> with multiple levels

---

## 11. Horizontal Rules

---

***

___

---

## 12. Tables (Markdown tables - may fall back to paragraph in current narko)

| Header 1 | Header 2 | Header 3 |
|----------|----------|----------|
| Cell 1   | Cell 2   | Cell 3   |
| Cell 4   | Cell 5   | Cell 6   |

| Left | Center | Right |
|:-----|:------:|------:|
| L1   | C1     | R1    |
| L2   | C2     | R2    |

---

## 13. Line Breaks and Paragraphs

This is paragraph one with some text.

This is paragraph two after a blank line.

This is a line  
with a manual line break (two spaces).

---

## 14. Escape Characters

\*Not italic\* and \**not bold**

\`Not code\` and \==not highlighted==

\$Not math\$ and \$$not block math$$

---

## 15. HTML-like Content (should be escaped)

<script>alert('test')</script>

<div>HTML div content</div>

<strong>HTML strong tag</strong>

---

## 16. Complex Combinations

### Task list with formatting
- [x] **Bold completed task** with *italic text*
- [ ] Task with `inline code` and ==highlighting==
- [ ] Task with [link](https://example.com) and $math$

### Code with math comments
```python
# Calculate E = mc^2
def energy_mass_relation(mass, c=299792458):
    """
    Famous equation: E = mc²
    """
    return mass * c ** 2
```

### Callout with complex content
> [!NOTE]
> This callout contains **bold text**, *italic text*, `code`, ==highlights==, 
> and even [links](https://example.com).
> 
> It also has multiple paragraphs and a task list:
> - [x] First task
> - [ ] Second task

---

## 17. Edge Cases

### Empty elements
- [ ] 
- [x] 

```

```

$$
$$

==== (not a highlight)

### Special characters in code
```bash
echo "Hello $USER"
grep -r "pattern" . | head -10
find . -name "*.py" -exec grep -l "import" {} \;
```

### Unicode and emoji
Unicode text: café, naïve, résumé 
Emojis: 🚀 🎉 ✅ ❌ 🔧 📝

---

## Summary

This comprehensive test covers:
- ✅ All CommonMark basic syntax (headers, text formatting, lists, links, code, blockquotes, horizontal rules)
- ✅ narko extensions (task lists, math blocks/inline, highlights, callouts)  
- ✅ Edge cases and complex combinations
- ✅ Potential error conditions

Expected behavior in Notion:
- Headers become heading blocks (max level 3)
- Text formatting preserved where supported
- Lists become bulleted/numbered list items
- Task lists become to-do blocks
- Code blocks preserve language and syntax
- Math blocks become equation blocks
- Math inline becomes code formatting
- Highlights get yellow background
- Callouts become callout blocks with appropriate icons
- Regular quotes become quote blocks
- Tables may fall back to paragraphs (known limitation)