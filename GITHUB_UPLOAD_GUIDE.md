# ICSFP GitHub上传指南

## 方法1: 使用Git凭据（推荐）

### 步骤1: 配置Git用户信息
```powershell
git config --global user.name "你的GitHub用户名"
git config --global user.email "你的GitHub邮箱"
```

### 步骤2: 使用Personal Access Token
由于GitHub已停止支持密码验证，你需要使用Personal Access Token

1. 访问 https://github.com/settings/tokens
2. 点击 "Generate new token (classic)"
3. 勾选 `repo` 权限
4. 生成并复制token

### 步骤3: 推送代码
```powershell
# 方式A: 在URL中包含token
git remote set-url icsfp https://你的token@github.com/Leo-610/ICSFP.git
git push icsfp master

# 方式B: 使用Git Credential Manager（推荐）
git push icsfp master
# 会弹出认证窗口，使用你的GitHub凭据登录
```

---

## 方法2: 使用GitHub Desktop（最简单）

1. 下载并安装 GitHub Desktop: https://desktop.github.com/
2. 登录你的GitHub账号
3. 在GitHub Desktop中：
   - File -> Add Local Repository
   - 选择 `D:\大创中期\HCSF`
   - 点击 "Publish repository"
   - Repository name: `ICSFP`
   - Description: "Intelligent Causal Stock Forecasting Platform"
   - 取消勾选 "Keep this code private" （如果要公开）
   - 点击 "Publish Repository"

---

## 方法3: 使用SSH密钥

### 步骤1: 生成SSH密钥
```powershell
ssh-keygen -t ed25519 -C "你的GitHub邮箱"
# 按Enter使用默认路径，设置密码（可选）
```

### 步骤2: 添加SSH密钥到GitHub
```powershell
# 复制公钥内容
cat ~/.ssh/id_ed25519.pub
```

1. 访问 https://github.com/settings/keys
2. 点击 "New SSH key"
3. 粘贴公钥内容
4. 保存

### 步骤3: 使用SSH推送
```powershell
# 添加SSH远程仓库
git remote set-url icsfp git@github.com:Leo-610/ICSFP.git

# 推送代码
git push icsfp master
```

---

## 方法4: 通过GitHub网页上传（适合小项目）

1. 访问 https://github.com/Leo-610/ICSFP
2. 点击 "uploading an existing file"
3. 将整个HCSF文件夹压缩成zip
4. 拖拽上传

**注意**: 此方法不保留Git历史记录

---

## 当前状态

✅ **已完成:**
- 所有文件已添加到暂存区
- 提交了一个commit: "feat: ICSFP Phase1 - API, Enhanced Predictor and Web UI"
- 添加了远程仓库: icsfp

⏳ **待完成:**
- 需要身份验证后推送到GitHub

---

## 验证上传成功

推送成功后，访问:
https://github.com/Leo-610/ICSFP

你应该能看到:
- ✅ 所有项目文件
- ✅ README_ICAST.md作为主页
- ✅ api/, static/, docs/ 等目录
- ✅ commit历史

---

## 后续步骤

上传成功后，你可以:

1. **添加README.md**（如果想要更好的首页展示）
```powershell
cp README_ICAST.md README.md
git add README.md
git commit -m "docs: add README"
git push icsfp master
```

2. **配置GitHub Pages**（发布Web界面）
- Settings -> Pages
- Source: Deploy from branch
- Branch: master / root
- 访问: https://leo-610.github.io/ICSFP

3. **添加GitHub Actions**（自动化测试）

---

## 常见问题

**Q: push时提示403错误**
A: 需要配置身份验证，参考上面的方法1或2

**Q: 如何更新代码？**
A: 
```powershell
git add .
git commit -m "描述更新内容"
git push icsfp master
```

**Q: 如何切换回原仓库？**
A:
```powershell
git push origin master  # 推送到原wenrui-jiang/HCSF仓库
```

---

## 推荐操作顺序

1. ✅ 使用**方法2 (GitHub Desktop)**最简单
2. 或使用**方法1**并创建Personal Access Token
3. 推送成功后配置README.md
4. 可选: 配置GitHub Pages展示Web界面

---

**需要帮助？告诉我你选择哪种方法，我可以提供详细指导！** 🚀
