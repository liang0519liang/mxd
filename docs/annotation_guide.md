# Phase 2 预标注准备：本地网页手动框选

可以。推荐使用 **Label Studio 的本地网页界面**：它在自己的 Windows 电脑上运行，然后浏览器打开本地地址，在画面上用鼠标拖拽矩形框并选择 `player`、`monster` 或 `loot`。这比仓促自研标注网页更稳定，并支持导出与复审。

> 这不是云端链接，也不会自动把游戏画面上传；是否联网取决于你的安装方式和浏览器环境。开始前仍应确认录像和截图的使用符合游戏规则与服务条款。

## 使用步骤

1. 创建虚拟环境并安装标注工具：`py -m venv .venv`、`.venv\Scripts\activate`、`pip install -r requirements-labeling.txt`。
2. 启动服务：`label-studio start`；终端会显示本地 URL，通常为 `http://localhost:8080`。用浏览器打开它，首次按界面创建本地账号。
3. 新建项目，导入 `training/label_studio_config.xml` 作为标注界面配置；它只提供三种矩形标签：绿色 `player`、红色 `monster`、黄色 `loot`。
4. 先由 Phase 2 的 `extract_frames.py` 产出帧，再导入图片。每个可见实例都画**紧贴可见像素主体**的矩形；部分遮挡的对象仍标注可见部分。不要给纯特效、伤害数字或 UI 图标打成 monster/loot。
5. 完成后在 Label Studio 的 Export 页面导出 YOLO 格式（如当前版本提供的格式名称不同，选择带 class id 和归一化矩形坐标的 YOLO detection 导出），并执行后续数据集校验脚本。

## 质量规则

- 同一帧中每个玩家、怪物、掉落物各标一次；不同怪物外观第一版仍统一为 `monster`。
- 覆盖玩家的站立、移动、攻击、瞬移、跳跃；覆盖怪物受击、运动、遮挡；掉落物要覆盖不同背景与密集堆叠。
- 先按**录像会话**分 train/val/test，再导入/导出，不能把同一视频的相邻帧随机分到测试集。
- 每个会话抽样复审；有疑问的框记录为待复审，不要用猜测替代标注。

Phase 1 不会调用 Label Studio，也不会发送任何游戏按键；本指南和 XML 仅为后续数据制作准备。
