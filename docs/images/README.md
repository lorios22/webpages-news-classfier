# Architecture Images

This directory contains visual documentation for the Enhanced Crypto & Macro News Pipeline architecture.

## Architecture Diagram

The main architecture diagram is embedded as a Mermaid diagram directly in the README.md file. This provides several advantages:

1. **Always Up-to-Date**: The diagram is part of the code and updates with changes
2. **Version Controlled**: Changes to architecture are tracked in git history  
3. **Interactive**: GitHub renders Mermaid diagrams natively
4. **Accessible**: No external image dependencies

## Mermaid Diagram Features

The architecture diagram includes:

- **Color-coded Components**: Different colors for MCP, Memory, Agents, APIs, and Output
- **Clear Data Flow**: Arrows showing how data moves through the system
- **Component Grouping**: Related components are visually grouped
- **Hierarchical Layout**: Shows the relationship between different system layers

## Regenerating the Diagram

The diagram is automatically rendered by GitHub when viewing the README.md. If you need to generate a static image:

1. **Online Tools**: Copy the Mermaid code to [mermaid.live](https://mermaid.live)
2. **VS Code**: Use the Mermaid Preview extension
3. **CLI Tools**: Use `mermaid-cli` to generate PNG/SVG files

```bash
# Install mermaid-cli
npm install -g @mermaid-js/mermaid-cli

# Generate PNG (if needed)
mmdc -i architecture.mmd -o architecture_diagram.png
```

## Updating the Architecture

When making changes to the system architecture:

1. Update the Mermaid diagram in README.md
2. Test the diagram renders correctly
3. Update component descriptions if needed
4. Commit changes with clear description

The diagram should reflect the current state of the system and be updated whenever:
- New components are added
- Data flows change  
- Integration patterns are modified
- New APIs or services are integrated 