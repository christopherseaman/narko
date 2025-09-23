# Common Features Test

Quick test of frequently used markdown features in narko.

## Text Formatting
**Bold text**, *italic text*, and `inline code`.

## Task Lists
- [x] Completed task
- [ ] Todo task

## Code Block
```python
def example():
    return "Hello World"
```

## Math
Inline math: $x = \frac{-b \pm \sqrt{b^2-4ac}}{2a}$

Block math:
$$
\int_0^\infty e^{-x^2} dx = \frac{\sqrt{\pi}}{2}
$$

## Callout
> [!NOTE]
> This is an important note with **bold** and *italic* text.

## Highlight
This text has ==highlighted portions== for emphasis.

## Quote
> This is a regular blockquote for attributed text.

## Table
| Feature | Status | Notes |
|---------|--------|-------|
| Headers | ✅ Working | All levels supported |
| Math | ✅ Working | Both inline and block |
| Tables | ❓ Testing | May fall back to text |

## Complex Mixed Lists
1. First numbered item
   - Nested bullet under number
     - [ ] Task nested under bullet
     - [x] Completed task nested under bullet
   - Another nested bullet with **bold text**
     1. Numbered item nested under bullet
     2. Another numbered nested item
2. Second numbered item
   - [x] Task directly under numbered item
     - Bullet nested under task
       - [ ] Task nested under bullet under task
   - [ ] Uncompleted task under numbered item
     1. Numbered item under task
        - Final bullet at deep level


## Images
![Narko Logo](https://via.placeholder.com/300x150/blue/white?text=Narko+Test+Image)

![Local Profile](profile.png)

*Note: Image embedding depends on file upload capabilities*

## Mermaid Diagrams
```mermaid
graph TD
    A[Markdown File] --> B[narko Parser]
    B --> C{Content Type}
    C -->|Text| D[Rich Text Block]
    C -->|Code| E[Code Block]
    C -->|Math| F[Equation Block]
    C -->|Task| G[Todo Block]
    D --> H[Notion Page]
    E --> H
    F --> H
    G --> H
```

```mermaid
sequenceDiagram
    participant U as User
    participant N as narko
    participant API as Notion API
    
    U->>N: Run with --import
    N->>N: Parse markdown
    N->>N: Convert to blocks
    N->>API: Create page
    API-->>N: Page created
    N-->>U: Success URL
```

## Link
Check out [narko on GitHub](https://github.com/user/narko) for more info.

