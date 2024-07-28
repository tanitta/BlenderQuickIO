import bpy
import os.path
import os
import copy
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty


# https://wiki.blender.org/wiki/Process/Addons/Guidelines/metainfo
bl_info = {
    "name": "QuickIO",
    "author": "tanitta",
    "version": (0, 0, 0),
    "blender": (2, 91, 0),
    "location": "Import-Export",
    "description": "QuickIO",
    "warning": "",
    "support": "COMMUNITY",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Import-Export"
}

def get_children(obj):
    children = []
    get_children_rec(children, obj)
    return children

def get_children_rec(arr, obj):
    for c in obj.children:
        arr.append(c)
        get_children_rec(arr, c)

def scene_has_valid_path(scene):
    if not "quick_io_project_path" in scene: return False
    if scene["quick_io_project_path"] == "": return False
    project_path = scene["quick_io_project_path"]
    return os.path.exists(project_path)

def object_has_valid_path(obj):
    if not "quick_io_file_path" in obj: return False
    return True

def redraw_properties_window(context):
    for window in bpy.context.window_manager.windows:
        screen = window.screen
        for area in screen.areas:
            if area.type == 'PROPERTIES':
                area.tag_redraw()
                break

class QUICKIO_OT_CreateProps(bpy.types.Operator):
    bl_idname = "object.quick_io_create_props"
    bl_label  = "CreateProps"
    bl_description = "description"

    def set_prop_to_obj(self, obj):
        print(obj.name)
        obj["quick_io_file_path"] = "$JOB/" + obj.name + ".fbx"
        obj["quick_io_ignore_trs_location"] = True
        obj["quick_io_ignore_trs_rotation"] = True
        obj["quick_io_ignore_trs_scale"] = False

    def execute(self, context):
        selecteds = context.selected_objects
        if not "quick_io_project_path" in context.scene:
            context.scene["quick_io_project_path"] = ""
            redraw_properties_window(context)

        if len(selecteds) <= 0: return {'CANCELLED'}
        for obj in selecteds:
            self.set_prop_to_obj(obj)
        redraw_properties_window(context)
        return {'FINISHED'}

class QUICKIO_OT_SetProjectPath(bpy.types.Operator, ImportHelper):
    bl_idname = "object.quick_io_set_project_path"
    bl_label  = "Set Project Path"
    bl_description = "description"

    filepath: StringProperty(
            name="project path",
            default="C:/",
            subtype= 'DIR_PATH'
            )
    filename_ext = ".fbx"
    is_relative: BoolProperty(
            name='Relative path from current .blend file',
            description='Relative path from current .blend file',
            default=False,
            )
    directory : StringProperty(default="C:/",subtype='DIR_PATH')

    def set_project_path(self, context, obj):
        job_path = context.scene["quick_io_project_path"]
        directory = self.directory
        if self.is_relative:
        # if True:
            current_blend_file = bpy.path.abspath('//')
            print("abs: " + current_blend_file)
            directory = os.path.relpath(directory, current_blend_file)
            abspath = os.path.normpath(os.path.join(current_blend_file, directory))
            print("abspath:" + abspath)
        context.scene["quick_io_project_path"] = str(directory)
        pass

    def execute(self, context):
        selecteds = context.selected_objects
        if not "quick_io_project_path" in context.scene:
            context.scene["quick_io_project_path"] = ""
            redraw_properties_window(context)

        if len(selecteds) != 1: return {'CANCELLED'}
        self.set_project_path(context, selecteds[0])
        redraw_properties_window(context)
        return {'FINISHED'}

class QUICKIO_OT_SetFilePath(bpy.types.Operator, ImportHelper):
    bl_idname = "object.quick_io_set_file_path"
    bl_label  = "Set File Path"
    bl_description = "description"

    filepath: StringProperty(
            name="file path",
            subtype= 'DIR_PATH'
            )
    filename_ext = ".fbx"
    filter_glob: StringProperty(
            default="*.fbx",
            options={'HIDDEN'},
            )

    is_relative: BoolProperty(
            name='Relative path from $JOB',
            description='Relative path from $JOB',
            default=True,
            )

    def set_file_path(self, context, obj):
        filepath = self.filepath
        if self.is_relative:
            job_path = context.scene["quick_io_project_path"]
            current_blend_file = bpy.path.abspath('//')
            full_job_path = os.path.normpath(os.path.join(current_blend_file, job_path))
            print("full_job_path: "+full_job_path)
            filepath = filepath.replace(full_job_path, '$JOB')
        obj["quick_io_file_path"] = filepath

    def execute(self, context):
        selecteds = context.selected_objects
        if not "quick_io_project_path" in context.scene:
            context.scene["quick_io_project_path"] = ""
            redraw_properties_window(context)

        if len(selecteds) != 1: return {'CANCELLED'}
        self.set_file_path(context, selecteds[0])
        redraw_properties_window(context)
        return {'FINISHED'}

class QUICKIO_OT_Import(bpy.types.Operator):
    bl_idname = "object.quick_io_import"
    bl_label  = "Import"
    bl_description = "description"

    def import_root_object(self, project_path, root):
        raw_file_path = root["quick_io_file_path"]
        file_path_expanded = raw_file_path.replace('$JOB', project_path)
        targets = get_children(root)
        targets.append(root)

        memo_root_name = root.name
        memo_location = copy.copy(root.location)
        memo_rotation = copy.copy(root.rotation_euler)
        memo_scale    = copy.copy(root.scale)
        memo_ignore_trs_location = root["quick_io_ignore_trs_location"]
        memo_ignore_trs_rotation = root["quick_io_ignore_trs_rotation"]
        memo_ignore_trs_scale    = root["quick_io_ignore_trs_scale"]

        # delete_targets
        for target in targets:
            target.delete()

        # import
        bpy.ops.import_scene.fbx(
            filepath=file_path_expanded,
        )

        new_root_obj = filter(lambda o: o.name == memo_root_name, bpy.context.scene.objects)[0]

        # rename
        new_root_obj.name = memo_root_name
        new_root_obj.location = memo_location
        new_root_obj.rotation_euler = memo_rotation
        new_root_obj.scale = memo_scale

        # set custom prop
        new_root_obj["quick_io_ignore_trs_location"] = memo_ignore_trs_location
        new_root_obj["quick_io_ignore_trs_rotation"] = memo_ignore_trs_rotation
        new_root_obj["quick_io_ignore_trs_scale"]    = memo_ignore_trs_scale

    def execute(self, context):
        selecteds = context.selected_objects
        if not scene_has_valid_path(context.scene): return {'CANCELLED'}
        if len(selecteds) <= 0: return {'CANCELLED'}

        project_path = context.scene["quick_io_project_path"]
        for obj in filter(lambda o: object_has_valid_path(o), selecteds):
            # if not self.object_has_valid_path(obj): continue
            self.import_root_object(project_path, obj)
        return {'FINISHED'}

def default_setting_path():
    user_path = bpy.utils.resource_path('USER')
    config_path = os.path.join(user_path, "scripts", "presets", "operator", "export_scene.fbx")
    return config_path

class QUICKIO_OT_Preferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    export_settings_path: bpy.props.StringProperty(
        name="ExportSettingPath",
        description="An export setting file(.py)",
        default = default_setting_path(),
        subtype='FILE_PATH'
    )

    def draw(self, context):
        layout = self.layout

        sp = layout.split(factor=0.3)
        col = sp.column()
        col.label(text="ExportSettingPath")
        col.prop(self, "export_settings_path", text="")

import ast
def load_settings_from_script(filepath, settings):
    with open(filepath, 'r') as file:
        # ファイルから不要な行を削除 (import文と'op ='の行)
        lines = [line.strip() for line in file if not line.startswith(('import', 'op ='))]
        # 各行から設定を抽出して辞書に格納
        for line in lines:
            if line.startswith('op.'):
                # 'op.'を削除して解析しやすくする
                line = line[3:]
                key, value = line.split(' = ')
                # 文字列の周りの余分なスペースを削除
                key = key.strip()
                value = value.strip()
                # evalを使ってPythonの式を安全に評価
                try:
                    # 安全な評価のためにリテラル評価を使用することを検討
                    settings[key] = ast.literal_eval(value)
                    # settings[key] = eval(value, {"__builtins__": {}}, {})
                except NameError:
                    # 評価に失敗した場合は値をそのまま格納
                    settings[key] = value
    return settings

class QUICKIO_OT_Export(bpy.types.Operator):
    bl_idname = "object.quick_io_export"
    bl_label  = "Export"
    bl_description = "description"


    def __init__(self):
        pass

    def export_root_object(self, project_path, root):
        targets = get_children(root)
        targets.append(root)
        self.export_object(project_path, root, targets)

    def export_object(self, project_path, root, targets):
        # deselect
        for obj in bpy.context.selected_objects:
            obj.select_set(False)

        # select exported target
        for obj in targets:
            obj.select_set(True)

        raw_file_path = root["quick_io_file_path"]
        if not os.path.isabs(project_path):
            current_blend_file = bpy.path.abspath('//')
            project_path = os.path.normpath(os.path.join(current_blend_file, project_path))
        file_path_expanded = raw_file_path.replace('$JOB', project_path)

        dirname = os.path.dirname(file_path_expanded)
        if not os.path.exists(dirname): os.makedirs(dirname)

        
        prefs = bpy.context.preferences.addons[__name__].preferences
        export_settings_path = prefs.export_settings_path
        if "export_settings_path" in obj and obj["export_settings_path"].strip() != "":
            export_settings_path = obj["export_settings_path"]

        export_settings = {}

        if os.path.isfile(export_settings_path):
            load_settings_from_script(export_settings_path, export_settings)

        memo_location = copy.copy(obj.location)
        memo_rotation = copy.copy(obj.rotation_euler)
        memo_scale    = copy.copy(obj.scale)
        if obj["quick_io_ignore_trs_location"]: obj.location       = [0.0, 0.0, 0.0]
        if obj["quick_io_ignore_trs_rotation"]: obj.rotation_euler = [0.0, 0.0, 0.0]
        if obj["quick_io_ignore_trs_scale"]:    obj.scale          = [1.0, 1.0, 1.0]

        export_settings["filepath"] = file_path_expanded
        export_settings["filter_glob"] = "*.fbx"
        export_settings["use_selection"] = True

        bpy.ops.export_scene.fbx(**export_settings)

        obj.location = memo_location
        obj.rotation_euler = memo_rotation
        obj.scale = memo_scale

        print("file_path_expanded: " + file_path_expanded)


    def execute(self, context):
        selecteds = context.selected_objects
        if not scene_has_valid_path(context.scene): return {'CANCELLED'}
        if len(selecteds) <= 0: return {'CANCELLED'}
        project_path = context.scene["quick_io_project_path"]
        for obj in filter(lambda o: object_has_valid_path(o), selecteds):
            # if not self.object_has_valid_path(obj): continue
            self.export_root_object(project_path, obj)

        # reselect
        for obj in bpy.context.selected_objects:
            obj.select_set(False)
        for obj in selecteds:
            obj.select_set(True)

        return {'FINISHED'}

class QUICKIO_PT_General(bpy.types.Panel):
    bl_label = "QuickIO"
    # https://docs.blender.org/api/current/bpy.types.Panel.html#bpy.types.Panel.bl_space_type 
    bl_space_type = "VIEW_3D"
    # https://docs.blender.org/api/current/bpy.types.Panel.html#bpy.types.Panel.bl_region_type 
    bl_region_type = "UI"
    # https://docs.blender.org/api/current/bpy.types.Panel.html#bpy.types.Panel.draw
    def draw(self, context):
        self.layout.operator(QUICKIO_OT_CreateProps.bl_idname)
        self.layout.operator(QUICKIO_OT_SetProjectPath.bl_idname)
        self.layout.operator(QUICKIO_OT_SetFilePath.bl_idname)
        self.layout.operator(QUICKIO_OT_Import.bl_idname)
        self.layout.operator(QUICKIO_OT_Export.bl_idname)

        obj = context.object
        
        if obj:
            row = self.layout.row()
            row.label(text="Custom Properties", icon='MODIFIER')
            
            for prop_name, prop_value in obj.items():
                row = self.layout.row()
                # 通常のプロパティではなく、IDプロパティを取得しているため '[]' を使用
                row.prop(obj, '["{}"]'.format(prop_name), text=prop_name)

classes = [ 
    QUICKIO_OT_CreateProps,
    QUICKIO_OT_SetFilePath,
    QUICKIO_OT_SetProjectPath,
    QUICKIO_OT_Import,
    QUICKIO_OT_Export,
    QUICKIO_PT_General,
    QUICKIO_OT_Preferences,
]

def register():
    for c in classes:
        bpy.utils.register_class(c)

def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)

if __name__ == "__main__":
    register()
