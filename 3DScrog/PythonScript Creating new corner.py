import bpy
import math

# --- Параметры цилиндров и вращения ---
internal_diameter = 2.78        # мм
external_diameter = 1.5 * internal_diameter  # мм
external_height = 28            # мм

# Параметры для сектора
inner_diameter = 28.0      # Внутренний диаметр (мм)
outer_diameter = 35.0      # Наружный диаметр (мм)
width = (outer_diameter - inner_diameter)
pos_tube = outer_diameter - width
height = 25.0              # Высота цилиндра (мм)
missing_sector_start = 0   # Начальный угол отсутствующего сектора (°)
missing_sector_end = 90    # Конечный угол отсутствующего сектора (°)
segments = 1024            # Количество сегментов для плавности
offset_of_joinded = 10     # Сдвиг объединённого объекта

def apply_boolean_difference(target_obj, cutter_obj):
    bool_mod = target_obj.modifiers.new(type='BOOLEAN', name='Bool_Cut')
    bool_mod.operation = 'DIFFERENCE'
    bool_mod.object = cutter_obj
    bpy.context.view_layer.objects.active = target_obj
    bpy.ops.object.modifier_apply(modifier=bool_mod.name)



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


def move_object(obj, shift_x=0.0, shift_y=0.0, shift_z=0.0):
    """Перемещает указанный объект на заданные смещения по осям X, Y, Z."""
    if obj is None:
        print("move_object: Объект не найден или не передан.")
        return
    
    # Переключение в режим объекта для безопасного изменения transform
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # Перемещаем объект
    obj.location.x += shift_x
    obj.location.y += shift_y
    obj.location.z += shift_z
    
    print(f"Объект '{obj.name}' перемещен на ({shift_x}, {shift_y}, {shift_z})")


def rotate_object(obj, angle_x_deg=0.0, angle_y_deg=0.0, angle_z_deg=0.0):
    """Поворачивает объект на заданные углы (в градусах) вокруг осей X, Y, Z."""
    if obj is None:
        print("rotate_object: Объект не найден или не передан.")
        return
    
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # Конвертация градусов в радианы
    angle_x_rad = math.radians(angle_x_deg)
    angle_y_rad = math.radians(angle_y_deg)
    angle_z_rad = math.radians(angle_z_deg)
    
    # Применение поворота к Эйлер-углам
    obj.rotation_euler[0] += angle_x_rad
    obj.rotation_euler[1] += angle_y_rad
    obj.rotation_euler[2] += angle_z_rad
    
    print(f"Объект '{obj.name}' повернут на X:{angle_x_deg}°, Y:{angle_y_deg}°, Z:{angle_z_deg}°")


def delete_all_objects():
    """Удаляет все объекты из текущей сцены."""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)


def polar_to_cartesian(radius, angle_rad, z):
    """Преобразует полярные координаты в декартовы."""
    x = radius * math.cos(angle_rad)
    y = radius * math.sin(angle_rad)
    return (x, y, z)


def create_hollow_cylinder(height, diameter, location=(0,0,0), rotation=(0,0,0), internal_diameter=2.8):
    """Создает полый цилиндр заданных параметров с помощью булевой операции."""
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # Создание внешнего цилиндра
    bpy.ops.mesh.primitive_cylinder_add(
        radius=diameter / 2,
        depth=height,
        location=location,
        rotation=rotation
    )
    external = bpy.context.active_object
    external.name = "External_Cylinder"
    
    # Создание внутреннего цилиндра для булевого вычитания
    bpy.ops.mesh.primitive_cylinder_add(
        radius=internal_diameter / 2,
        depth=height + 0.2,  # Чуть больше для избежания артефактов
        location=location,
        rotation=rotation
    )
    internal = bpy.context.active_object
    internal.name = "Internal_Cylinder"
    
    # Применение булевой операции (Difference)
    bool_mod = external.modifiers.new(type='BOOLEAN', name='Bool_Hollow')
    bool_mod.operation = 'DIFFERENCE'
    bool_mod.object = internal
    
    bpy.context.view_layer.objects.active = external
    bpy.ops.object.modifier_apply(modifier=bool_mod.name)
    
    # Удаление внутреннего цилиндра
    bpy.data.objects.remove(internal, do_unlink=True)
    
    return external

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



# --- Основная логика ---

# Удаляем все объекты в сцене
delete_all_objects()

# Перевод диаметров в радиусы
inner_radius = inner_diameter / 2.0
outer_radius = outer_diameter / 2.0

# Перевод углов в радианы
start_rad = math.radians(missing_sector_end)
end_rad = math.radians(missing_sector_start)
angle_range = (end_rad - start_rad) % (2 * math.pi)

vertices = []
faces = []

# Создание вершин для нижней и верхней части цилиндра с отсутствующим сектором
for i in range(segments + 1):
    angle = start_rad + angle_range * i / segments
    # Нижняя грань (Z=0)
    vertices.append(polar_to_cartesian(outer_radius, angle, 0))
    vertices.append(polar_to_cartesian(inner_radius, angle, 0))
    # Верхняя грань (Z=height)
    vertices.append(polar_to_cartesian(outer_radius, angle, height))
    vertices.append(polar_to_cartesian(inner_radius, angle, height))

# Создание граней боковых поверхностей и крышек
for i in range(segments):
    outer_bottom1 = 4 * i
    inner_bottom1 = 4 * i + 1
    outer_bottom2 = 4 * (i + 1)
    inner_bottom2 = 4 * (i + 1) + 1
    outer_top1 = 4 * i + 2
    inner_top1 = 4 * i + 3
    outer_top2 = 4 * (i + 1) + 2
    inner_top2 = 4 * (i + 1) + 3

    # Наружная боковая грань
    faces.append((outer_bottom1, outer_bottom2, outer_top2, outer_top1))
    # Внутренняя боковая грань
    faces.append((inner_bottom2, inner_bottom1, inner_top1, inner_top2))
    # Нижняя поверхность
    faces.append((outer_bottom1, inner_bottom1, inner_bottom2, outer_bottom2))
    # Верхняя поверхность
    faces.append((outer_top1, inner_top1, inner_top2, outer_top2))

# Добавление плоскостей для закрытия отсутствующего сектора (крышки)
cap_vertices = []

# Координаты углов отсутствующего сектора на нижней грани
cap_vertices.append(polar_to_cartesian(outer_radius, start_rad, 0))
cap_vertices.append(polar_to_cartesian(inner_radius, start_rad, 0))
cap_vertices.append(polar_to_cartesian(inner_radius, end_rad, 0))
cap_vertices.append(polar_to_cartesian(outer_radius, end_rad, 0))

# Координаты углов отсутствующего сектора на верхней грани
cap_vertices.append(polar_to_cartesian(outer_radius, start_rad, height))
cap_vertices.append(polar_to_cartesian(inner_radius, start_rad, height))
cap_vertices.append(polar_to_cartesian(inner_radius, end_rad, height))
cap_vertices.append(polar_to_cartesian(outer_radius, end_rad, height))

base_start = len(vertices)
vertices.extend(cap_vertices[:4])

top_start = len(vertices)
vertices.extend(cap_vertices[4:])

# Нижняя крышка
faces.append((base_start, base_start + 1, top_start + 1, top_start))
# Верхняя крышка
faces.append((base_start + 2, base_start + 3, top_start + 3, top_start + 2))

# Создание меша и объекта
mesh = bpy.data.meshes.new("Hollow_Cylinder_With_Missing_Sector")
mesh.from_pydata(vertices, [], faces)
mesh.update()

obj = bpy.data.objects.new("Hollow_Cylinder_With_Missing_Sector", mesh)
bpy.context.collection.objects.link(obj)

# Нормализация нормалей
bpy.context.view_layer.objects.active = obj
bpy.ops.object.select_all(action='DESELECT')
obj.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.normals_make_consistent(inside=False)
bpy.ops.object.mode_set(mode='OBJECT')

# Создаем и модифицируем основные цилиндры
main_cyl1 = create_hollow_cylinder(
    height=external_height,
    diameter=external_diameter,
    location=(0, 0, external_height / 2),
    rotation=(0, 0, 0),
    internal_diameter=internal_diameter
)

rotate_object(main_cyl1, angle_x_deg=90, angle_y_deg=0, angle_z_deg=90)
move_object(main_cyl1, shift_x=-pos_tube, shift_y=0)

main_cyl2 = create_hollow_cylinder(
    height=external_height,
    diameter=external_diameter,
    location=(0, 0, external_height / 2),
    rotation=(0, 0, 0),
    internal_diameter=internal_diameter
)

rotate_object(main_cyl2, angle_x_deg=90, angle_y_deg=0, angle_z_deg=180)
move_object(main_cyl2, shift_x=0, shift_y=-pos_tube)

all_objects = [obj] + [main_cyl1] + [main_cyl2]

collection_name = "Collection"

collection = group_into_collection(all_objects, collection_name)

# Объединение объектов в один
joined_obj = join_objects(collection)

rotate_object(joined_obj, angle_x_deg=-90, angle_y_deg=45, angle_z_deg=0)

move_object(joined_obj, shift_x=0, shift_y=0, shift_z=offset_of_joinded)


# Создание плоскости-вырезателя (куба)
cut_cube = create_cut_plane(cut_thickness=10, size=100, z_offset=-3)

# Применение булевой вырезки
apply_boolean_difference(joined_obj, cut_cube)

# Удаление плоскости-вырезателя
bpy.data.objects.remove(cut_cube, do_unlink=True)

print("Скрипт успешно завершён.")
