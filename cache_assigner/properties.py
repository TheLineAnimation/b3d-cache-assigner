
import bpy
import os
from bpy.types import PropertyGroup, Operator
from bpy.props import StringProperty, BoolProperty, CollectionProperty, IntProperty, EnumProperty, PointerProperty


from . import preferences

import re
from collections import defaultdict
from pathlib import Path

from .utils import LoggerFactory, PathUtils

logger = LoggerFactory.get_logger()

class ScanForAlembicFiles(Operator):
    bl_idname = "object.scan_for_alembic_files"
    bl_label = "Scan for Blend Files"

    def extract_and_reorder_filename(self, filename):
        try:
            # Regex pattern to capture parts of the filename
            pattern = re.compile(r"(3d_anim|3d_layout)_(.*?)_3d_rigging.*__(v\d{3})\.")

            # Match the pattern in the filename
            match = pattern.search(filename)
            if not match:
                return filename

            # Extract parts from the regex groups
            task_name = match.group(1)
            asset_name = match.group(2)
            version = match.group(3)
            extension = filename.rsplit('.', 1)[1]


            # Extract the type (animation, layout, etc.) before 3d_anim_
            type_match = re.search(r"tre_sh\d+_(.*?)_(3d_anim|3d_layout)_", filename)
            if not type_match:
                return filename
            
            type_name = type_match.group(1)

            # Extract the item number before the version
            item_number_match = re.search(r"_(\d{2})__", filename)
            if not item_number_match:
                return filename

            item_number = item_number_match.group(1)

            # Create the new string
            new_string = f"{task_name}_{asset_name}_{item_number}_{type_name}_{version}.{extension}"

            logger.info (f'NICE NAME {match.groups()} {asset_name} {item_number} {version} {extension}')


            return new_string
        except Exception as e:
            # In case of any unexpected error, return the original filename
            return filename

    def get_latest_versions(self,files):
        file_dict = defaultdict(list)
        
        # Regular expression to capture the filename and version number
        pattern = re.compile(r"^(.*?)(v\d{3})$")

        for file_path in files:
            match = pattern.search(file_path.stem)
            if match:
                base_name = match.group(1)
                version = match.group(2)
                file_dict[base_name].append((version, file_path))
        
        latest_files = []
        for base_name, versions in file_dict.items():
            latest_version = max(versions, key=lambda x: int(x[0][1:]))
            latest_files.append(latest_version[1])
        
        return latest_files
    
    def scan_for_abc_files(self, directory, context):

        lookProps = context.scene.CacheAssignerProperties
        lookProps.abc_files.clear()

        directory_path = Path(directory)
        all_files = list(directory_path.rglob("*.abc"))
        
        if lookProps.latest_files_only:
            files_to_process = self.get_latest_versions(all_files)
        else:
            files_to_process = all_files
        
        for file_path in files_to_process:
            logger.debug(f'ScanForAlembicFiles - File Found: {file_path.parent} {file_path.name}')

            if lookProps.nice_name:
                display_name = self.extract_and_reorder_filename(file_path.name) 
            else:
                display_name = file_path.name

            item = lookProps.abc_files.add()
            item.name = file_path.name
            item.display_name = display_name
            item.path = str(file_path)
            
        lookProps.abc_file_index = -1

    def execute(self, context):
        prefs =  preferences.get(context) 
        lookProps = context.scene.CacheAssignerProperties  
        selected_path = PathUtils.get_anim_from_shot_context(self)
        self.scan_for_abc_files(selected_path, context)

        return {'FINISHED'}

def alembic_item_clicked (self,context):
    """
    handler here just in case the UI needed to do anything when the file is highlighted
    """
    cacheProps = context.scene.CacheAssignerProperties 
    abc_file_index = cacheProps.abc_file_index
    if abc_file_index >= 0 and abc_file_index < len(cacheProps.abc_files):
        abc_file_path = cacheProps.abc_files[abc_file_index].path
        logger.debug (f'abc File clicked - {abc_file_path}')

def update_alembic_list( self, context):
    bpy.ops.object.scan_for_alembic_files()

class AlembicFileItem(PropertyGroup):
    name: StringProperty(name="File Name",default="")
    display_name: StringProperty(name="Display Name",default="")
    path: StringProperty(name="File Path",default="")

class CacheAssignerProperties(PropertyGroup):
    abc_files : CollectionProperty(type=AlembicFileItem )

    abc_file_index : IntProperty(name="Index for abc_files", default=-1, update=alembic_item_clicked)
    # highest_version : IntProperty(name="The current highest version of the caches", default=0 )

    # nice_name : BoolProperty(name="Nice Name", default=False)
    nice_name : BoolProperty(name="Nice Name", default=False, update=update_alembic_list)

    latest_files_only : BoolProperty(name="Latest Files Only", default=False, update=update_alembic_list)
    task_root : StringProperty(name="Context Path", default="", get=PathUtils.get_anim_from_shot_context)

    asset_name : StringProperty(
        name="Asset / Shot Name",
        description="Category in 3D View Toolbox where the Export panel is displayed",
        default="",
        get=PathUtils.get_asset_name
    )

    task_name: StringProperty(
        name="Task Name",
        description="Category in 3D View Toolbox where the Export panel is displayed",
        default="",
        get=PathUtils.get_task_name
    )

    full_project_name: StringProperty(
        name="Project Name",
        description="Name of the project on Pype and Ftrack",
        default="",
        get=PathUtils.get_project_name
    )

    work_path_name: StringProperty(
        name="Work Path",
        description="Category in 3D View Toolbox where the Export panel is displayed",
        default="",
        get=PathUtils.get_work_path
    )



def register():
    bpy.utils.register_class(ScanForAlembicFiles)
    bpy.utils.register_class(AlembicFileItem)
    bpy.utils.register_class(CacheAssignerProperties)
    bpy.types.Scene.CacheAssignerProperties = PointerProperty(type=CacheAssignerProperties)



def unregister():
    
    bpy.utils.unregister_class(ScanForAlembicFiles)
    bpy.utils.unregister_class(AlembicFileItem)
    bpy.utils.unregister_class(CacheAssignerProperties)
    del bpy.types.Scene.CacheAssignerProperties



