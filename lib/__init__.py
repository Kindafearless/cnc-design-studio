"""
CNC library - Machine configuration and shared utilities for Shapeoko 5 Pro
"""

from .shapeoko import (
    MachineConstraints,
    Tolerances,
    StockSizes,
    ToolType,
    Tool,
    TOOL_LIBRARY,
    CuttingParams,
    check_part_fits,
    get_tool,
    list_tools,
)

__all__ = [
    "MachineConstraints",
    "Tolerances",
    "StockSizes",
    "ToolType",
    "Tool",
    "TOOL_LIBRARY",
    "CuttingParams",
    "check_part_fits",
    "get_tool",
    "list_tools",
]
