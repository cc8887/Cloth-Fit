# 赤云长袍 V4 源衣复刻

这里保留实际使用的 Blender 调形代码、源衣静态诊断、区域分类与不贴紧掩码。它们基于精确的 CloudCoat 三角网格顶点顺序，不适用于任意 OBJ 或 FBX。生成模型只留在本地，请遵守上游输入的适用条款；参见 [素材说明](../../NOTICES.md)。

## 从已取得的上游输入生成

在根目录运行。需要 Blender（本轮验证为 4.3.2），并先取得固定提交的 Cloth-fit 上游；可以只下载输入仓库，生成源衣本身不需要编译求解器：

```bash
git clone https://github.com/Huangzizhou/cloth-fit cloth-fit
git -C cloth-fit checkout --detach 123e2440f46720b5f993c91d1705aff838aa55fb
CONTROLS=1 bash tools/build_structured.sh cloth-fit local-inputs/rebuilt
(cd local-inputs/rebuilt/v4 && sha256sum -c ../../../source/structured/input.sha256)
```

- [V2 脚本](../base/build_coat.py) 从 `garment-data/assets/garments/Puffer_dense/` 读取 `garment.obj` 和 `skeleton.obj`，保持共同拓扑基准，重塑立领和袖口并延长下摆。与历史代码相比，只增加了输入、输出目录的配置方式。
- [V4 调形脚本](structure_coat.py) 原样保留。默认胸 .34、腰 .37、腹 .33、袖 .24、摆 .18、顺形 .68。它保留 UV、面和顶点编号，只移动顶点并生成求解掩码。固定字节校验覆盖 3,472 顶点、6,840 三角面、2,265 个不贴紧区顶点和 4,232 个完全落在该区内的三角面。此包里的 `no-fit.txt` 和 `zone_indices.json` 仅含作者自己划定的零基索引子集，不含点位、连边、面序列或纹理。
- `CONTROLS=1` 另外生成六组单参数变体，并在本地建立带独立形态键的 `CloudCoat_Structured.blend`。它重建版型和滑块，不重建旧版参考图、红云贴图与渲染。组合滑块只是预览，最终输入直接用 `structure_coat.py` 和相同拓扑重新生成，再做静态后检查。脚本只写入新的输出目录。
- 若已持有合规的原 V2 输入，可跳过第一步建模：`blender -b -t 2 --python-exit-code 1 -P source/structured/structure_coat.py -- --base /path/to/your/V2 --out local-inputs/custom-v4`。必须有 `garment.obj`、`source_skeleton.obj`、`cloud_coat.blend`。不要只换同顶点数的网格；开口、固定坐标带、肩袖骨骼编号同样须匹配。

## 求解与静态复查

```bash
bash tools/bootstrap.sh
python3 tools/reproduce.py FoxGirl --structured-source local-inputs/rebuilt/v4
python3 tools/reproduce.py Goblin --structured-source local-inputs/rebuilt/v4
# N 为 metrics.json 中该次运行的最新步；以下以历史 FoxGirl 的 174 为例。
blender -b --factory-startup --python-exit-code 1 -P qa/blender_static_overlap.py -- \
  runs/FoxGirl/output/step_garment_174.obj runs/FoxGirl/output/target_avatar.obj
```

`qa/` 收录历史范围量、边长/拓扑、结果日志、坐标还原、UV 回配、Blender BVH 检查和 IPC 检查源文件；详见 [后检查说明](../../qa/README.md)。当前复测重建了本地 V4 源输入及形态键，未重编 Cloth-fit 或重跑历史完整优化；README 的实际试穿耗时和比较值来自此前的六次运行记录。
