# 静态复核工具

- `blender_static_overlap.py`：以 Blender BVH 分别筛查衣物与角色之间的相交三角对、衣物非邻接三角形相交。输入必须在同一坐标空间，服装在前，人体在后。详见[源衣复刻步骤](../source/structured/README.md)。
- `validate_structured_ipc.cpp`：历史 V4 使用的 IPC 复核源文件。依赖与固定版本 Cloth-fit 相同的 IPC/Libigl C++ 环境，输入顺序为人体、衣服。不是便携可执行文件；需要在已有上游 C++ 构建环境中单独编译链接。Blender BVH 无需编译。
- `mesh_audit.py`、`check_finish.py`：分别检查有限三角网格与索引、以及旧版运行目录的日志和导出是否完整。后者按历史 `garment_final.obj` / `run.log` 目录格式工作。
- `measure_gap.py`：对两份同体型、同衣服拓扑的已整理案例计算与人体表面的距离，Blender 脚本参数为 `旧目录 新目录 zone_indices.json 输出JSON`。每个案例目录需按历史文件名放置同一坐标空间中的 `avatar.obj` 和 `garment_final.obj`。 `shape_metrics.py` 比较分区包围大小和相邻三角面角度分位；需要 NumPy，用 `--help` 查看参数。指标不是面料刚度，也不是动作验证。
- `restore_target_coordinates.py`：将求解器归一化的衣服带回原始人体轴向和尺度。必须使用 `target_avatar.obj`，不能使用迭代期间的变形人体；需要 NumPy。
- `styled_export.py`：只在三角面的顶点编号严格对应时回配调用者自己的 UV；不改变求解顶点。用于适用素材的本地展示，不创建或提供纹理。

未检出静态交叉并不代表蒙皮、动作或加厚后没有穿插。
