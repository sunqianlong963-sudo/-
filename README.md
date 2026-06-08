# 口才能力测评 · 自测工具

一个纯前端的口才能力自测网页，打开即用，无需后端、无需任何 API 密钥。

- 6 大能力维度（心理素质 / 口脑协调 / 条理表达 / 抓取重点 / 简洁表达 / 主题升华）
- 12+1 道题，约 2 分钟完成
- 本地算分生成报告，可一键保存为图片

## 在线使用

> https://sunqianlong963-sudo.github.io/-/

## 如何开启在线链接（首次，约 1 分钟）

GitHub 静态托管（Pages）首次需要在网页上手动开启一次：

1. 打开仓库 **Settings（设置）→ 左侧 Pages**
2. **Build and deployment → Source** 选择 **Deploy from a branch（从分支部署）**
3. **Branch** 选择 `claude/quirky-cray-L93jQ`，文件夹保持 `/ (root)`，点 **Save**
4. 等 1～2 分钟，刷新该页面，顶部会出现网址：
   `https://sunqianlong963-sudo.github.io/-/`

开启后，以后只要往该分支推送改动，页面会自动重新发布，无需再设置。

## 其他部署方式

整个工具就是单个 `index.html`，也可以直接拖到任意静态托管（对象存储、虚拟主机、Vercel、Netlify 等）使用。
