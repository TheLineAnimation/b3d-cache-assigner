import bpy
from bpy.types import Operator, AddonPreferences, PropertyGroup
from bpy.props import StringProperty, CollectionProperty, IntProperty, BoolProperty

import os
import json
import logging

from .utils import LoggerFactory
logger = LoggerFactory.get_logger()

class AlembicFilePathItem(PropertyGroup):
    name: StringProperty(
        name="Name",  
        description="If this has been loaded from an external file, it will have a Python logo instead of a folder."
        )
    file_path: StringProperty(
        name="File Path", 
        subtype='DIR_PATH', 
        default=""
        )


class CacheAssignerPreferences(AddonPreferences):
    bl_idname = "cache_assigner"

    task_filter: StringProperty(name="Task Filter", default="animation")

    debug_mode: BoolProperty(
        name="Debugging Mode",
        default=True,
        update=lambda self, context: self.update_logging_level()
    )

    def update_logging_level(self):
        if self.debug_mode:
            LoggerFactory.set_level(logging.DEBUG)
            logger.debug("Debug Logger Enabled")
        else:
            LoggerFactory.set_level(logging.INFO)

    def draw(self, context):
        layout = self.layout
        # layout.prop(self, "task_filter", text="Task Filter")
        layout.prop(self, "debug_mode", text="Enable Debugging Mode (Check system console for extra messages)")

def get(context: bpy.types.Context) -> CacheAssignerPreferences:
    """Return the add-on preferences."""
    prefs = context.preferences.addons["cache_assigner"].preferences
    assert isinstance(
        prefs, CacheAssignerPreferences
    ), "Expected CacheAssignerPreferences, got %s instead" % (type(prefs))
    return prefs

  
def register():
    bpy.utils.register_class(AlembicFilePathItem)
    bpy.utils.register_class(CacheAssignerPreferences)

def unregister():
    bpy.utils.unregister_class(CacheAssignerPreferences)
    bpy.utils.unregister_class(AlembicFilePathItem)
