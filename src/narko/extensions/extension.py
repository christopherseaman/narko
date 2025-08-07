"""
Main Notion extension for Marko
"""
from marko.helpers import MarkoExtension
from .blocks import MathBlock, CalloutBlock, TaskListItem, FileUploadBlock
from .inline import Highlight, InlineMath


# Create the Notion Extension
NotionExtension = MarkoExtension(
    elements=[
        MathBlock, 
        CalloutBlock, 
        TaskListItem, 
        FileUploadBlock, 
        Highlight, 
        InlineMath
    ]
)