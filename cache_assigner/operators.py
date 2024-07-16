import bpy
import os
from bpy.types import Operator
from bpy.props import IntProperty
import math
import re

from . import utils
from . import preferences

from .utils import LoggerFactory
logger = LoggerFactory.get_logger()

class LoadAlembicCacheFromFile(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "object.load_alembic_cache_from_file"
    bl_label = "Load Alembic"

    # @classmethod
    # def poll(cls, context):
    #     return context.active_object is not None and context.scene.CacheAssignerProperties.abc_files and len(context.scene.CacheAssignerProperties.abc_files) > 0

    def execute(self, context):   
        selObj = bpy.context.object
        cacheProps = context.scene.CacheAssignerProperties 

        if selObj:
            currentCol = selObj.users_collection
            objColl = selObj.users_collection
            mesh_objs = (list(currentCol)[0].objects.values())
            abcDataBlock = None 
 
            if 'MeshSequenceCache' in selObj.modifiers:
                if selObj.modifiers['MeshSequenceCache'].cache_file:
                    abcDataBlock = selObj.modifiers['MeshSequenceCache'].cache_file.name
                else:
                    self.report({'ERROR'}, "Couldn't find a datablock to remap the sequence cache. Make sure you have loaded an Alembic file.")
            else:
                self.report({'ERROR'}, "I couldn't a Mesh sequence cache modifier. Please add one and load a base file to continue...")

            logger.debug (f'abc DataBlock {abcDataBlock}')
            
            if abcDataBlock: 

                abc_file_index = cacheProps.abc_file_index
                if abc_file_index >= 0 and abc_file_index < len(cacheProps.abc_files):
                    abc_file_path = cacheProps.abc_files[abc_file_index].path
                else:
                    return
                # get the alembic file from the datablock name   
                abcFile = bpy.data.cache_files[abcDataBlock]
                # set the abc filepath                
                abcFile.filepath = abc_file_path

                # make sure you reload the datablock, otherwise the object paths will not resolve
                bpy.ops.cachefile.reload() 

                for obj in mesh_objs:  
                    if 'MeshSequenceCache' in obj.modifiers:                                  
                            obj.modifiers['MeshSequenceCache'].cache_file = abcFile
                            abcPath = abcFile.object_paths   

                            for cacheObjPath in abcPath.items():                                                                                     
                                # print (f'CACHE PATH - {cacheObjPath}')
                                path= cacheObjPath[0]
                                # need to split the object from any instancing
                                base_object_name = obj.name.split('.')[0]
                                if base_object_name in path:
                                    obj.modifiers['MeshSequenceCache'].cache_file = abcFile                                   
                                    obj.modifiers['MeshSequenceCache'].object_path = path     
                                    # logger.debug (f'MATCH - OBJ {obj.name} {base_object_name}\n\tABC PATH {path}')                        
                                else:
                                    pass
                                    # logger.debug (f'NO MATCH - BASE {base_object_name} OBJ {obj.name}\n\t PATH - {path}')

        return {'FINISHED'}

    
class OBJECT_OT_purge_unused_caches(bpy.types.Operator):
    """Purge Unused Materials"""
    bl_idname = "object.purge_unused_caches"
    bl_label = "Purge Unused Caches"
    bl_options = {'REGISTER', 'UNDO'}

    # @classmethod
    # def poll(cls, context):
    #     return True
        # context.area.type == 'VIEW_3D'

    def execute(self, context):
        # Iterate over all materials and remove those with no users
        # materials_to_remove = [mat for mat in bpy.data.materials if mat.users == 0]

        # for mat in materials_to_remove:
        #     bpy.data.materials.remove(mat)
        
        # self.report({'INFO'}, f"Removed {len(materials_to_remove)} unused materials.")
        return {'FINISHED'}


class_list = [
    OBJECT_OT_purge_unused_caches,
    LoadAlembicCacheFromFile,
]

def register():    
    for cls in class_list:
        bpy.utils.register_class(cls)


def unregister():
    for cls in class_list:
        bpy.utils.unregister_class(cls)

