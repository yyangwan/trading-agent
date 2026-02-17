# 系统发布与部署指南

## 一、发布到GitHub流程

### 步骤1：准备代码仓库
```bash
# 1. 清理临时文件和敏感信息
cd /root/.openclaw/workspace/stock_picker

# 2. 创建.gitignore文件
cat > .gitignore << 'EOF'
# 敏感配置
configs/system_config.yaml
configs/strategies_config.yaml.local

# 数据文件
data/
data/cache/
data/backups/

# 输出文件
output/
output/picks/
output/backtests/

# 日志文件
logs/
*.log

# Python缓存
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
*.so

# 虚拟环境
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# 系统文件
.DS_Store
Thumbs.db
EOF

# 3. 创建配置文件模板
cp configs/system_config.yaml configs/system_config.yaml.example
cp configs/strategies_config.yaml configs/strategies_config.yaml.example

# 4. 编辑模板文件，删除敏感信息（如token）
# 将token字段改为：token: "YOUR_TUSHARE_TOKEN_HERE"
```

### 步骤2：你需要在GitHub上操作

**请你完成以下操作：**

1. **创建GitHub仓库**
   - 访问 https://github.com/new
   - 仓库名建议：`stock-picker` 或 `a-share-stock-picker`
   - 设置为 Public 或 Private（根据你的需求）
   - **不要**初始化 README、.gitignore 或 LICENSE
   - 点击"Create repository"

2. **获取仓库地址**
   - 创建后会显示仓库地址，格式如：
   - `https://github.com/你的用户名/stock-picker.git`

**然后告诉我仓库地址，我来完成后续操作。**

---

### 步骤3：我需要你提供的信息

请回复以下信息：

1. **GitHub仓库地址**
   - 示例：`https://github.com/zhangchao/stock-picker.git`

2. **GitHub用户名**
   - 示例：`zhangchao`

3. **GitHub Token**（如果启用了双因素认证）
   - 在 GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
   - 创建新 Token，勾选 `repo` 权限
   - 如果不需要，我可以尝试用你的账号密码

4. **确认敏感信息已清理**
   - 确认 `system_config.yaml` 中的 token 已删除或替换为占位符
   - 确认没有其他敏感配置（如数据库密码、API密钥等）

---

## 二、部署到新服务器流程

### 方案A：新服务器已有OpenClaw（推荐）

```bash
# 1. 克隆代码
cd ~/.openclaw/workspace
git clone https://github.com/你的用户名/stock-picker.git
cd stock_picker

# 2. 安装依赖
pip3 install -r requirements.txt

# 3. 配置系统
cp configs/system_config.yaml.example configs/system_config.yaml
vim configs/system_config.yaml  # 填写你的配置

# 4. 测试
python3 main.py --test

# 5. 设置定时任务（可选）
crontab -e
# 添加：30 15 * * 1-5 cd ~/.openclaw/workspace/stock_picker && python3 main.py >> logs/cron.log 2>&1
```

### 方案B：新服务器没有OpenClaw

```bash
# 1. 安装Python环境
sudo yum install -y python3 python3-pip

# 2. 安装TA-Lib（技术指标库）
wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib/
./configure --prefix=/usr
make
sudo make install
cd ..

# 3. 克隆代码
git clone https://github.com/你的用户名/stock-picker.git
cd stock_picker

# 4. 安装Python依赖
pip3 install -r requirements.txt

# 5. 配置
cp configs/system_config.yaml.example configs/system_config.yaml
vim configs/system_config.yaml

# 6. 测试
python3 main.py --test
```

---

## 三、你需要配合的操作清单

### 阶段1：发布前准备

- [ ] **确认敏感信息已清理**
  - 检查 `configs/system_config.yaml` 中的 token
  - 检查是否有数据库密码、API密钥等
  - 所有敏感信息替换为占位符（如 `YOUR_TOKEN_HERE`）

- [ ] **决定GitHub仓库类型**
  - Public：任何人可见
  - Private：只有你可见（需要GitHub付费账户）

- [ ] **创建GitHub仓库**
  - 访问 https://github.com/new
  - 输入仓库名称
  - 选择 Public/Private
  - **不要**初始化 README

### 阶段2：发布时

- [ ] **提供GitHub仓库地址**
  - 格式：`https://github.com/用户名/仓库名.git`

- [ ] **提供GitHub凭据**（如果需要）
  - 用户名
  - Token 或密码

### 阶段3：部署到新服务器

- [ ] **提供新服务器访问信息**
  - IP地址
  - SSH用户名
  - SSH密码/密钥

- [ ] **确认新服务器环境**
  - 是否已安装 OpenClaw？
  - 操作系统版本（如 CentOS/Ubuntu）

---

## 四、自动化部署脚本（可选）

我可以为你创建一键部署脚本：

```bash
#!/bin/bash
# deploy.sh

set -e

echo "🚀 开始部署选股系统..."

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 未安装Python3，请先安装"
    exit 1
fi

# 克隆代码
if [ -d "stock_picker" ]; then
    echo "📁 目录已存在，拉取最新代码..."
    cd stock_picker
    git pull
else
    echo "📁 克隆代码仓库..."
    git clone https://github.com/你的用户名/stock-picker.git
    cd stock_picker
fi

# 安装依赖
echo "📦 安装依赖..."
pip3 install -r requirements.txt

# 配置文件
if [ ! -f "configs/system_config.yaml" ]; then
    echo "⚙️ 创建配置文件..."
    cp configs/system_config.yaml.example configs/system_config.yaml
    echo "✅ 请编辑 configs/system_config.yaml 填写你的配置"
fi

# 测试
echo "🧪 测试系统..."
python3 main.py --test

echo "✅ 部署完成！"
```

---

## 五、我需要你现在回复的信息

请按以下格式回复：

```
1. GitHub仓库地址：https://github.com/xxx/stock-picker.git
2. GitHub用户名：xxx
3. GitHub Token：（可选，如果需要）
4. 是否已清理敏感信息：是/否
5. 新服务器IP：（如果需要部署）
6. 新服务器SSH用户：（如果需要部署）
```

---

## 六、后续维护

发布到GitHub后，你可以：

1. **版本管理**
   - 使用 Git Tag 标记版本
   - 查看变更历史
   - 回滚到旧版本

2. **多服务器同步**
   - 每次修改后 `git pull` 即可更新
   - 保持多台服务器代码一致

3. **团队协作**（如果开源）
   - 接受 Pull Request
   - 问题追踪
   - Wiki 文档

**等待你的GitHub仓库地址，我立即完成发布！**
