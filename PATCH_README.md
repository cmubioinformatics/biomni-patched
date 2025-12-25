# Biomni 补丁包

这是从 conda 环境 `biomni_e1` 中提取的修改后的 biomni 包代码。

## 安装方法

### 方法 1: 直接覆盖安装（推荐）

```bash
# 激活环境
conda activate biomni_e1

# 备份原始包
cp -r /data/ag_reichart_lindberg/home/xin/anaconda3/envs/biomni_e1/lib/python3.11/site-packages/biomni \
      /data/ag_reichart_lindberg/home/xin/anaconda3/envs/biomni_e1/lib/python3.11/site-packages/biomni.original

# 删除旧包
rm -rf /data/ag_reichart_lindberg/home/xin/anaconda3/envs/biomni_e1/lib/python3.11/site-packages/biomni

# 安装新包
cp -r /data/ag_reichart_lindberg/home/xin/project/biomni-patched/biomni \
      /data/ag_reichart_lindberg/home/xin/anaconda3/envs/biomni_e1/lib/python3.11/site-packages/
```

### 方法 2: 使用 pip 编辑模式安装

```bash
# 激活环境
conda activate biomni_e1

# 卸载原包
pip uninstall biomni -y

# 以可编辑模式安装补丁包
cd /data/ag_reichart_lindberg/home/xin/project/biomni-patched
pip install -e .
```

### 方法 3: 在新环境中安装

```bash
# 创建新环境
conda create -n biomni_custom python=3.11 -y
conda activate biomni_custom

# 安装原始 biomni（从原始仓库）
pip install git+https://github.com/snap-stanford/Biomni.git

# 然后用补丁包覆盖
rm -rf /data/ag_reichart_lindberg/home/xin/anaconda3/envs/biomni_custom/lib/python3.11/site-packages/biomni
cp -r /data/ag_reichart_lindberg/home/xin/project/biomni-patched/biomni \
      /data/ag_reichart_lindberg/home/xin/anaconda3/envs/biomni_custom/lib/python3.11/site-packages/
```

## 修改记录

根据文件修改时间，主要修改包括：
- `biomni/agent/a1.py` - Agent 主逻辑
- `biomni/tool/support_tools.py` - 支持工具
- `biomni/tool/literature.py` - 文献工具

## 注意事项

1. 此补丁包只包含代码，不包含数据和模型文件
2. 数据和模型需要单独配置
3. 安装前建议备份原始环境
