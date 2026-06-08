# 口才能力测评 · 自测工具

一个纯前端的口才能力自测网页，打开即用，无需后端、无需任何 API 密钥。

- 6 大能力维度（心理素质 / 口脑协调 / 条理表达 / 抓取重点 / 简洁表达 / 主题升华）
- 12+1 道题，约 2 分钟完成
- 本地算分生成报告，可一键保存为图片

## 在线使用

部署在 GitHub Pages：

> https://sunqianlong963-sudo.github.io/-/

## 部署说明

本仓库已配置 GitHub Actions 自动部署（`.github/workflows/deploy-pages.yml`）。
若首次部署需要手动开启，可在仓库 **Settings → Pages → Build and deployment → Source**
选择 **GitHub Actions** 即可。

整个工具就是单个 `index.html`，也可以直接用任意静态托管（如把文件拖到对象存储 / 任意虚拟主机）。
