# 眼力试炼：真假识破

一个微信 H5 小游戏原型，考验你的眼力与决策能力。

## 游戏说明

在有限信用点下，判断两张相似图片中哪张是假的（或哪张是真的）。随着难度递增，你需要更快速地做出判断。

### 核心机制
- 10 点信用点，每回合消耗 1 点，用完即结束
- 10-15 回合，每回合倒计时 3 秒（后期缩短到 2 秒）
- 正确 +100 分，错误 -50 分
- 1.5 秒内回答额外 +50 速度分
- 难度递增：R1-5 找不同（假图有明显改动）、R6-10 找相同（真图有细微差别）、R11-15 混合模式

### 特色
- 纯静态 HTML/CSS/JS，无需 npm 安装
- 移动端优先，大按钮，竖屏体验
- Canvas 生成动态图形，每次对局都有不同
- 结算页面生成分享文案，适合群聊晒分

## 快速运行

### 方法 1：直接打开
在浏览器中打开 `index.html` 即可试玩。

### 方法 2：本地服务器
```bash
python3 -m http.server 8000
# 然后访问 http://localhost:8000
```

## GitHub Pages 部署

1. Fork 本仓库或创建新仓库
2. 推送代码到 `main` 分支
3. 在仓库 Settings → Pages 中：
   - Source: GitHub Actions
   - 选择 `.github/workflows/deploy-pages.yml`
4. GitHub Actions 会自动部署，访问 `https://你的用户名.github.io/仓库名/`

### 自动部署工作流
仓库已包含 `.github/workflows/deploy-pages.yml`，配置使用 GitHub Actions 自动部署 Pages：

```yaml
name: Deploy to GitHub Pages
on:
  push:
    branches: [ main ]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Pages
        uses: actions/configure-pages@v4
      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: '.'
      - name: Deploy to Pages
        uses: actions/deploy-pages@v4
```

## 项目结构
```
├── index.html    # 主页面
├── style.css     # 样式
├── game.js       # 游戏逻辑
├── README.md     # 说明文档
├── AGENTS.md     # 项目元信息
└── DESIGN.md     # 设计文档
```

## 技术栈
- HTML5 Canvas（图形生成）
- CSS3 Flexbox + Grid（响应式布局）
- Vanilla JavaScript（无框架依赖）

## 许可
MIT License - 自由修改和发布。

---

**提示**：这是快速原型，可以进一步扩展更多图形类型、音效、排行榜等功能。
