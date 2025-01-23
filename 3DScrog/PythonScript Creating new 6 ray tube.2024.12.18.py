import bpy
import math

# --- 1. Параметры цилиндров и вращения ---
internal_diameter = 2.85  # мм
external_diameter = 1.75 * internal_diameter  # мм
external_height = 33     # мм
rotation_angles = [
    (90, 'X'),  # Угол в градусах и ось для первой копии
    (90, 'Y')   # Угол в градусах и ось для второй копии
]

# --- 2. Функция для очистки сцены ---
def clear_scene():
    # Удаление всех объектов из всех коллекций
    for collection in bpy.data.collections:
        for obj in collection.objects:
            bpy.data.objects.remove(obj, do_unlink=True)
    # Удаление всех коллекций кроме мастер-коллекции
    for collection in bpy.data.collections:
        if collection.name != "Collection":
            bpy.data.collections.remove(collection, do_unlink=True)

# --- 3. Установка единиц измерения в миллиметры ---
def set_units_mm():
    scene = bpy.context.scene
    scene.unit_settings.system = 'METRIC'
    scene.unit_settings.scale_length = 0.001  # 1 Blender unit = 1 мм

# --- 4. Функция для создания полого цилиндра ---
def create_hollow_cylinder(height, diameter, location=(0,0,0), rotation=(0,0,0), internal_diameter=2.8):
    # Создание внешнего цилиндра
    bpy.ops.mesh.primitive_cylinder_add(
        radius=diameter / 2,
        depth=height,
        location=location,
        rotation=rotation
    )
    external = bpy.context.active_object
    external.name = "External_Cylinder"
    
    # Создание внутреннего цилиндра для булевой операции
    bpy.ops.mesh.primitive_cylinder_add(
        radius=internal_diameter / 2,
        depth=height + 0.2,  # Немного больше для избежания артефактов
        location=location,
        rotation=rotation
    )
    internal = bpy.context.active_object
    internal.name = "Internal_Cylinder"
    
    # Применение булевой вырезки
    bool_mod = external.modifiers.new(type='BOOLEAN', name='Bool_Hollow')
    bool_mod.operation = 'DIFFERENCE'
    bool_mod.object = internal
    bpy.context.view_layer.objects.active = external
    bpy.ops.object.modifier_apply(modifier=bool_mod.name)
    
    # Удаление внутреннего цилиндра
    bpy.data.objects.remove(internal, do_unlink=True)
    
    return external

# --- 5. Функция для создания и поворота копий ---
def create_rotated_copies(original_obj, angles):
    copies = []
    for angle_deg, axis in angles:
        # Копирование объекта
        copy = original_obj.copy()
        copy.data = original_obj.data.copy()
        bpy.context.collection.objects.link(copy)
        
        # Установка поворота
        angle_rad = math.radians(angle_deg)
        rot = [0, 0, 0]
        axis_idx = {'X': 0, 'Y': 1, 'Z': 2}.get(axis.upper(), 0)
        rot[axis_idx] = angle_rad
        copy.rotation_euler = tuple(rot)
        
        copies.append(copy)
    return copies

# --- 6. Функция для группировки объектов в коллекцию ---
def group_into_collection(objects, collection_name):
    collection = bpy.data.collections.get(collection_name)
    if not collection:
        collection = bpy.data.collections.new(collection_name)
        bpy.context.scene.collection.children.link(collection)
    for obj in objects:
        # Удаление объекта из всех коллекций
        for coll in obj.users_collection:
            coll.objects.unlink(obj)
        collection.objects.link(obj)
    return collection

# --- 7. Функция для объединения объектов в один ---
def join_objects(collection):
    objs = [obj for obj in collection.objects if obj.type == 'MESH']
    if not objs:
        print(f"В коллекции '{collection.name}' нет объектов для объединения.")
        return None
    
    # Активный объект для объединения
    bpy.context.view_layer.objects.active = objs[0]
    
    # Выбор объектов
    for obj in objs:
        obj.select_set(True)
    
    # Объединение объектов
    bpy.ops.object.join()
    joined = bpy.context.active_object
    joined.name = "Joined_Object"
    return joined

# --- 8. Функция для поворота объекта ---
def rotate_object(obj, angle_x_deg=0, angle_y_deg=0, angle_z_deg=0):
    angle_x_rad = math.radians(angle_x_deg)
    angle_y_rad = math.radians(angle_y_deg)
    angle_z_rad = math.radians(angle_z_deg)
    obj.rotation_euler[0] += angle_x_rad
    obj.rotation_euler[1] += angle_y_rad
    obj.rotation_euler[2] += angle_z_rad
    obj.keyframe_insert(data_path="rotation_euler", frame=bpy.context.scene.frame_current)

# --- 9. Функция для создания плоскости-вырезателя ---
def create_cut_plane(cut_thickness=1, size=100, z_offset=3):
    # Создание куба, который будет выступать как плоскость-вырезатель
    bpy.ops.mesh.primitive_cube_add(
        size=1,  # Начальный размер
        location=(0, 0, z_offset)
    )
    cut_cube = bpy.context.active_object
    # Установка размеров куба
    cut_cube.scale = (size, size, cut_thickness / 2)  # Толщина по Z
    cut_cube.name = "Cut_Cube"
    return cut_cube

# --- 10. Функция для применения булевой вырезки ---
def apply_boolean_difference(target_obj, cutter_obj):
    bool_mod = target_obj.modifiers.new(type='BOOLEAN', name='Bool_Cut')
    bool_mod.operation = 'DIFFERENCE'
    bool_mod.object = cutter_obj
    bpy.context.view_layer.objects.active = target_obj
    bpy.ops.object.modifier_apply(modifier=bool_mod.name)

# --- 11. Функция для удаления объекта ---
def delete_object(obj):
    bpy.data.objects.remove(obj, do_unlink=True)

# --- Основной блок выполнения ---
def main():
    # Очистка сцены и установка единиц измерения
    clear_scene()
    set_units_mm()
    
    # Создание основного полого цилиндра, расположенного так, чтобы основание на Z=0
    main_cyl = create_hollow_cylinder(
        height=external_height,
        diameter=external_diameter,
        location=(0, 0, external_height / 2),  # Центрирование цилиндра по Z
        rotation=(0, 0, 0),
        internal_diameter=internal_diameter
    )
    
    # Создание и поворот копий
    copies = create_rotated_copies(main_cyl, rotation_angles)
    
    # Группировка всех цилиндров в коллекцию
    all_cylinders = [main_cyl] + copies
    collection_name = "Intersecting_Cylinders"
    collection = group_into_collection(all_cylinders, collection_name)
    
    # Объединение объектов в один
    joined_obj = join_objects(collection)
    if not joined_obj:
        return  # Прерывание, если объединение не удалось
    
    # Поворот объединённого объекта
    rotate_object(joined_obj, angle_x_deg=45, angle_y_deg=-35.26, angle_z_deg=0)
    
    # Создание плоскости-вырезателя (куба)
    cut_cube = create_cut_plane(cut_thickness=6.5, size=100, z_offset=6.5)
    
    # Применение булевой вырезки
    apply_boolean_difference(joined_obj, cut_cube)
    
    # Удаление плоскости-вырезателя
    delete_object(cut_cube)
    
    print("Скрипт выполнен успешно: объект создан, вырезан и плоскость удалена.")

# Запуск основного блока
if __name__ == "__main__":
    main()
