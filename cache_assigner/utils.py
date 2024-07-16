import bpy
import sys
import logging
import os
import re

from pathlib import Path
from collections import defaultdict

class LoggerFactory:
    """
    A class to handle logging for the Blender addon.
    """

    LOGGER_NAME = "CacheAssignerLogger"
    FORMAT_DEFAULT = "[%(name)s][%(levelname)s] %(message)s"
    LEVEL_DEFAULT = logging.INFO
    PROPAGATE_DEFAULT = True
    _logger_obj = None

    @classmethod
    def get_logger(cls):
        """
        Returns the singleton logger object, creating it if necessary.
        """
        if cls._logger_obj is None:
            cls._logger_obj = logging.getLogger(cls.LOGGER_NAME)
            cls._logger_obj.setLevel(cls.LEVEL_DEFAULT)
            cls._logger_obj.propagate = cls.PROPAGATE_DEFAULT

            fmt = logging.Formatter(cls.FORMAT_DEFAULT)
            stream_handler = logging.StreamHandler(sys.stdout)
            stream_handler.setFormatter(fmt)
            cls._logger_obj.addHandler(stream_handler)
        
        return cls._logger_obj

    @classmethod
    def set_level(cls, level):
        """
        Sets the logging level of the logger.
        """
        logger = cls.get_logger()
        logger.setLevel(level)
        
    @classmethod
    def set_propagate(cls, propagate):
        """
        Sets the propagation property of the logger.
        """
        logger = cls.get_logger()
        logger.propagate = propagate

    @classmethod
    def debug(cls, msg, *args, **kwargs):
        cls.get_logger().debug(msg, *args, **kwargs)

    @classmethod
    def info(cls, msg, *args, **kwargs):
        cls.get_logger().info(msg, *args, **kwargs)

    @classmethod
    def warning(cls, msg, *args, **kwargs):
        cls.get_logger().warning(msg, *args, **kwargs)

    @classmethod
    def error(cls, msg, *args, **kwargs):
        cls.get_logger().error(msg, *args, **kwargs)

    @classmethod
    def critical(cls, msg, *args, **kwargs):
        cls.get_logger().critical(msg, *args, **kwargs)

    @classmethod
    def log(cls, level, msg, *args, **kwargs):
        cls.get_logger().log(level, msg, *args, **kwargs)

    @classmethod
    def exception(cls, msg, *args, **kwargs):
        cls.get_logger().exception(msg, *args, **kwargs)

    @classmethod
    def write_to_file(cls, path, level=logging.WARNING):
        """
        Writes log messages to a specified file.
        """
        file_handler = logging.FileHandler(path)
        file_handler.setLevel(level)

        fmt = logging.Formatter("[%(asctime)s][%(levelname)s] %(message)s")
        file_handler.setFormatter(fmt)

        logger = cls.get_logger()
        logger.addHandler(file_handler)

logger = LoggerFactory.get_logger()

def ShowMessageBox(message = "", title = "Message Box", icon = 'INFO'):

    def draw(self, context):
        self.layout.label(text=message)

    bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)

class PathUtils: 

    def get_anim_from_shot_context(self):
        open_pype_work_dir = os.getenv("AVALON_WORKDIR") 
        animation_dir = Path(open_pype_work_dir).parent.parent / 'publish' / 'animation'  
        logger.debug (f'Animation Directory {animation_dir}') 
        return str(animation_dir) if not None else ""
    
    def get_project_path(self):
        open_pype_server_root = os.getenv("OPENPYPE_PROJECT_ROOT_WORK") 
        open_pype_project = os.getenv("AVALON_PROJECT")
        
        if open_pype_server_root and open_pype_project:  
            project_path = Path() / open_pype_server_root / open_pype_project
            logger.debug(f'PathUtils.get_project_path - {project_path}')
            return str(project_path)
        else:
            return ""
 
    def get_work_path(self): 
        return os.getenv("AVALON_WORKDIR")
         
    def get_project_name(self): 
        return os.getenv("AVALON_PROJECT")

    def get_task_name(self):
        return os.getenv("AVALON_TASK")
 
    def get_asset_name(self):
        return os.getenv("AVALON_ASSET")

# some testing methods for version change notification. Blender is pretty infuriating to code this for, 
# as the event loop on the UI is constantly firing. Don't know how to solve this one
class VersionChecker:

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
 
    def extract_version(self, filename):
        # This regex pattern will match the 2 or 3-digit version number at the end of the filename or the parent folder
        version_pattern = r'_v(\d{2,3})\.abc$'
        match = re.search(version_pattern, filename)
        if match:
            return int(match.group(1))
        else:
            raise ValueError("No version found in filename")
        
    def get_matched_files(self, filename, file_list):

        #extract the filename from the full path
        file_name_only = Path(filename).name

        logger.info(f'file_list: {file_list}')

        current_version = self.extract_version(file_name_only)
        logger.info(f'current cache version: {current_version}')
        
        # Extract the base filename without the version and extension
        base_filename_pattern = r'(.+)_v\d{2,3}\.abc$'
        base_match = re.match(base_filename_pattern, file_name_only)

        if not base_match:
            error_msg = "Filename format is incorrect"
            logger.error(error_msg)
            return error_msg

        base_filename = base_match.group(1)
        logger.info(f'Base filename: {base_filename}')

        
        filtered_file_list = []

        if file_list:
            for file in file_list:
                file_list_name_only = Path(filename).name      

                logger.info(f' PRE CHECK {base_filename}  {file_list_name_only} ')


                if base_filename in file_list_name_only:         
                # file_base_match = re.match(base_filename_pattern, file_list_name_only)
                # if file_base_match and file_base_match.group(1) == base_filename:

                    file_version = self.extract_version(file_list_name_only)

                    logger.info(f'file_version LOOP: {file_list_name_only} current {current_version} matched {file_version} ')

                    if file_version > current_version:
                        
                        filtered_file_list.append(file)
                        logger.info(f'ADDED: {file_list_name_only}')                                      
                        # file_version = self.extract_version(file)
                        # if file_version > highest_version:
                        #     highest_version = file_version
                        #     logger.info(f'Extracted higher version {file_version} from file {file}')
        return filtered_file_list
    
    def compare_versions(self, filename, file_list):

        highest_version = 0

        if not filename:
            return "Filename not present"
        
        try:
            current_version = self.extract_version(filename)
            logger.info(f'Current version extracted from filename: {current_version}')
            highest_version = current_version
        except ValueError as e:
            logger.error(e)
            return str(e)

        # Extract the base filename without the version and extension
        base_filename_pattern = r'(.+)_v\d{2,3}\.abc$'
        base_match = re.match(base_filename_pattern, filename)

        if not base_match:
            error_msg = "Filename format is incorrect"
            logger.error(error_msg)
            return error_msg

        base_filename = base_match.group(1)
        logger.debug(f'Base filename: {base_filename}')

        if file_list:
            for file in file_list:
                file_base_match = re.match(base_filename_pattern, file)
                if file_base_match and file_base_match.group(1) == base_filename:                    
                        file_version = self.extract_version(file)
                        if file_version > highest_version:
                            highest_version = file_version
                            logger.info(f'Extracted higher version {file_version} from file {file}')



        return highest_version
    
if __name__ == "__main__":
    
    LoggerFactory.set_propagate(False)

    LoggerFactory.debug("debug message")
    LoggerFactory.info("info message")
    LoggerFactory.warning("warning message")
    LoggerFactory.error("error message")
    LoggerFactory.critical("critical message")

