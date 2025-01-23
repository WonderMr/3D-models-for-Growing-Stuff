import bpy

def main():
    # Размеры в метрах
    CYLINDER1_HEIGHT = 0.04    # 40 мм
    CYLINDER1_DIAMETER = 0.115 # 115 мм

    CYLINDER2_HEIGHT = 0.002   # 2 мм
    CYLINDER2_DIAMETER = 0.125 # 125 мм

    CYLINDER3_HEIGHT = 0.003   # 3 мм
    CYLINDER3_DIAMETER = 0.118 # 98 мм

    CYLINDER4_HEIGHT = 0.003   # 3 мм
    CYLINDER4_DIAMETER = 0.118 # 98 мм

    CYLINDER5_HEIGHT = 1.0     # 1 м
    CYLINDER5_DIAMETER = 0.110 # 92 мм

    # 1. Очищаем сцену
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

    # 2. Создаем cylinder1 высотой 40 мм и диаметром 95 мм
    bpy.ops.mesh.primitive_cylinder_add(radius=CYLINDER1_DIAMETER / 2, depth=CYLINDER1_HEIGHT)
    cylinder1 = bpy.context.active_object

    # 3. Создаем cylinder2 высотой 3 мм и диаметром 115 мм
    bpy.ops.mesh.primitive_cylinder_add(radius=CYLINDER2_DIAMETER / 2, depth=CYLINDER2_HEIGHT)
    cylinder2 = bpy.context.active_object

    # 4. Создаем cylinder3 высотой 3 мм и диаметром 98 мм, размещаем его на верхней грани cylinder1
    cylinder3_z = (CYLINDER1_HEIGHT / 2) + (CYLINDER3_HEIGHT / 2)
    bpy.ops.mesh.primitive_cylinder_add(
        radius=CYLINDER3_DIAMETER / 2,
        depth=CYLINDER3_HEIGHT,
        location=(0, 0, cylinder3_z)
    )
    cylinder3 = bpy.context.active_object

    # 5. Создаем cylinder4 высотой 3 мм и диаметром 98 мм, размещаем его на нижней грани cylinder1
    cylinder4_z = -(CYLINDER1_HEIGHT / 2) - (CYLINDER4_HEIGHT / 2)
    bpy.ops.mesh.primitive_cylinder_add(
        radius=CYLINDER4_DIAMETER / 2,
        depth=CYLINDER4_HEIGHT,
        location=(0, 0, cylinder4_z)
    )
    cylinder4 = bpy.context.active_object

    # 6. Группируем cylinder1, cylinder2, cylinder3 и cylinder4 в один объект
    bpy.ops.object.select_all(action='DESELECT')
    cylinder1.select_set(True)
    cylinder2.select_set(True)
    cylinder3.select_set(True)
    cylinder4.select_set(True)
    bpy.context.view_layer.objects.active = cylinder1
    bpy.ops.object.join()
    combined_cylinder = bpy.context.active_object  # Объединённый объект

    # 7. Создаем cylinder5 диаметром 92 мм и высотой 1 м
    # Размещаем его так, чтобы он пересекал combined_cylinder по оси Z
    cylinder5_z = 0  # Центрируем по оси Z
    bpy.ops.mesh.primitive_cylinder_add(
        radius=CYLINDER5_DIAMETER / 2,
        depth=CYLINDER5_HEIGHT,
        location=(0, 0, cylinder5_z)
    )
    cylinder5 = bpy.context.active_object

    # 8. Вырезаем cylinder5 из combined_cylinder и удаляем cylinder5
    # Убедимся, что combined_cylinder активен
    bpy.ops.object.select_all(action='DESELECT')
    combined_cylinder.select_set(True)
    bpy.context.view_layer.objects.active = combined_cylinder

    # Применяем булевый модификатор
    bool_mod = combined_cylinder.modifiers.new(name='Boolean', type='BOOLEAN')
    bool_mod.operation = 'DIFFERENCE'
    bool_mod.object = cylinder5
    # Устанавливаем режим решения булевой операции
    bool_mod.solver = 'FAST'  # Или 'EXACT' при необходимости
    bpy.ops.object.modifier_apply(modifier=bool_mod.name)

    # Удаляем cylinder5
    bpy.data.objects.remove(cylinder5, do_unlink=True)
    
    #
    WALL_THICKNESS = 0.0018  # Толщина стенки в метрах (1.5 мм)
    # После объединения цилиндров и применения трансформаций
    bpy.context.view_layer.objects.active = combined_cylinder
    solidify_mod = combined_cylinder.modifiers.new(name='Solidify', type='SOLIDIFY')
    solidify_mod.thickness = WALL_THICKNESS  # Устанавливаем желаемую толщину стенки
    solidify_mod.offset = -1  # Чтобы толщина добавлялась внутрь объекта
    solidify_mod.use_flip_normals = True  # Переворачиваем нормали, если необходимо
    bpy.ops.object.modifier_apply(modifier=solidify_mod.name)


if __name__ == "__main__":
    main()
