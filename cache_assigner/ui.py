import bpy
from . import bl_info
from bpy.types import Panel, UIList, Operator

from . import preferences
import re
from pathlib import Path
from .utils import LoggerFactory, VersionChecker

from collections import defaultdict

logger = LoggerFactory.get_logger()

class AlembicFilePanel(Panel):
    bl_label = f"The Line - Cache Assigner v{bl_info['version'][0]}.{bl_info['version'][1]}.{bl_info['version'][2]}"
    bl_idname = "OBJECT_PT_cache_assigner"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "modifier"
   
    @classmethod
    def poll(cls, context):   
        # return 'MeshSequenceCache' in (item[0] for item in context.active_object.modifiers.items())
        # active = context.active_object is not None and 'MeshSequenceCache' in (item[0] for item in context.active_object.modifiers.items())

        return 'MeshSequenceCache' in (item[0] for item in context.active_object.modifiers.items())
   
    def text_row(self, parent, text, icon, label, factor):
        split = parent.split(factor=factor)
        split.label(text=text , icon=icon)
        split.label(text=label)

    def extract_version(self, filename):
        # This regex pattern will match the 2 or 3-digit version number at the end of the filename or the parent folder
        version_pattern = r'_v(\d{3})\.abc$'
        match = re.search(version_pattern, filename)
        if match:
            return int(match.group(1))
        else:
            raise ValueError("No version found in filename")
        
    def get_latest_versions(self, files):
        file_dict = defaultdict(list)        
        # Regular expression to capture the filename and version number
        pattern = re.compile(r"^(.*?)(v\d{3})\.abc$")
        for file_path in files:
            match = pattern.search(file_path)
            if match:
                base_name = match.group(1)
                version = match.group(2)
                file_dict[base_name].append((version, file_path))
        
        latest_files = []
        for base_name, versions in file_dict.items():
            latest_version = max(versions, key=lambda x: int(x[0][1:]))
            latest_files.append(latest_version[1])
        return latest_files
    
    def find_pattern_in_list(self, pattern, string_list):
        for string in string_list:
            if pattern in string:
                return string
        return None

    def get_current_alembic_file (self):
        selObj = bpy.context.object

        if selObj:
            abcDataBlock = None  
            if 'MeshSequenceCache' in selObj.modifiers:
                if selObj.modifiers['MeshSequenceCache'].cache_file:
                    abcDataBlock = selObj.modifiers['MeshSequenceCache'].cache_file.name
                else:
                    logger.debug("I couldn't find a datablock to remap the sequence cache. Make sure you have loaded an Alembic file.")
            else:
                logger.debug( "I couldn't find a Mesh sequence cache modifier. Please add one and load a base file to continue...")

            if abcDataBlock: 
                # get the alembic file from the datablock name   
                abcFile = bpy.data.cache_files[abcDataBlock]
                # get the abc filepath                
                # logger.debug( f'Current Alembic File = {abcFile.filepath}')

                path_data = Path(abcFile.filepath)
                file_data = {}
                file_data["name"] = path_data.name
                file_data["full_path"] = path_data.parent
                file_data["version"] = self.extract_version(path_data.name)

                return file_data
        
    def draw(self, context):

        cacheProps = context.scene.CacheAssignerProperties
        current_cache_file = self.get_current_alembic_file()

        layout = self.layout

        grid = layout.grid_flow(columns=2, align=True)
        grid.label(text=f"Project : {cacheProps.full_project_name}", icon='WORKSPACE')
        grid.label(text=f"Shot : {cacheProps.asset_name}", icon='COLLECTION_COLOR_05')
        grid.label(text=f"Task :{cacheProps.task_name}", icon='BRUSH_DATA')

        message = None
        icon_status = "INFO"

        try:
            if cacheProps.abc_files:
                if current_cache_file:
                    filtered_paths = [item.name for item in cacheProps.abc_files.values()]       
                    latest_version_caches = self.get_latest_versions(filtered_paths)
                    logger.debug(f'latest_version_caches {latest_version_caches}')
                    base_filename_pattern = r'(.+)_v\d{2,3}\.abc$'
                    base_match = re.match(base_filename_pattern, current_cache_file['name'])

                    icon_status = "INFO"
                    icon_colour = "SEQUENCE_COLOR_04"
                    message = f"You have the most up-to-date animation loaded."
                    
                    if base_match and base_match.group(1):
                        base_filename = base_match.group(1)
                        logger.debug(f'base_filename {base_filename}')
                        matching_cache = self.find_pattern_in_list(base_filename , latest_version_caches)
                        logger.debug(f'matching_cache {matching_cache}')
                        if matching_cache:
                            latest_version = self.extract_version(matching_cache)
                            logger.debug(f'latest_version is {latest_version}')

                            if latest_version > current_cache_file['version']:
                                icon_status = "ERROR"
                                icon_colour = "SEQUENCE_COLOR_01"
                                message = f"There is new animation present for this asset. Latest Cache : v{latest_version:03}:"
                    
                    grid.label(text=f"Loaded Version : v{current_cache_file['version']:03}", icon=icon_colour)
            else:
                message = "Click the button below to view the available cache files."

        except Exception as e:
            logger.debug(f'Caught Exception in Draw Function {e}')
            
        box = layout.box()

        if message:
            col = box.column()
            col.label(text=message, icon=icon_status)

        col = box.column()
        col.scale_y = 1.5
        col.operator( "object.scan_for_alembic_files", text="Get Cache Files", icon="FILE_FOLDER")   
        max_rows = 6
        abc_files_count = len(cacheProps.abc_files)
        set_height = lambda number: max_rows if number > max_rows else (0 if number < 0 else number)

        if abc_files_count > 0:
            num_rows = set_height (abc_files_count) + 1
            # panel_height = num_rows * row_height + 14
            display_str = "Alembic Cache" if abc_files_count == 1 else "Alembic Caches"
            layout.label(text=f"Found {abc_files_count} {display_str}:")

            layout.template_list("ALEMBIC_UL_FILE_LIST", "", cacheProps, "abc_files", cacheProps, "abc_file_index", type='DEFAULT', columns=1, rows=num_rows)

            box = layout.box()
            box.label(text='Load Filters')
            grid = box.grid_flow(columns=2, align=True)   
            grid.prop( cacheProps, "latest_files_only", text="Show latest versions", icon="EMPTY_SINGLE_ARROW")
            grid.prop( cacheProps, "nice_name", text="Show nice names", icon="FONT_DATA")

            col = layout.column()
            col.scale_y = 1.5
            col.operator("object.load_alembic_cache_from_file", text="Load Alembic File", icon="FILE_CACHE") 

    def draw_header(self, context):
        layout = self.layout
        layout.label(text="", icon='FILE_CACHE')


class ALEMBIC_UL_FILE_LIST(UIList):
    """Custom UI list to show blend files with icons"""
    
    def draw_item(self, context, layout, data, item, icon, active_data, active_property, index):
        cacheProps = context.scene.CacheAssignerProperties
       
        abc_file = item
        display_text = abc_file.display_name if cacheProps.nice_name else abc_file.name

        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.label(text=display_text, icon='FILE_CACHE')
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon='FILE_CACHE')

class_list = [
    AlembicFilePanel,
    ALEMBIC_UL_FILE_LIST,
]

def register():    

    for cls in class_list:
        bpy.utils.register_class(cls)

def unregister():

    for cls in class_list:
        bpy.utils.unregister_class(cls)


