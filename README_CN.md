# InstaPPT

**InstaPPT** 是一款由 AI 驱动的 PowerPoint 翻译工具，旨在提供高质量翻译的同时，完美保留幻灯片的原始视觉效果。

## 主要功能

- **AI 智能翻译：** 利用先进的大语言模型（如 GPT-4, DeepSeek）进行准确、上下文感知的翻译。
- **视觉保真：** 自动保留字体、颜色、大小和排版布局。
- **视觉对照报告：** 生成左右对照的 PDF 报告，以图片形式展示翻译前后的幻灯片，确保“所见即所得”，避免字体渲染问题。
- **智能缓存：** 自动缓存翻译结果，重复运行时节省成本和时间。
- **跨平台支持：** 支持 macOS（已优化）和 Windows。

## 环境要求

1.  **Python 3.10+**
2.  **LibreOffice:** 用于将 PPTX 转换为 PDF。
    -   macOS: `brew install --cask libreoffice`
    -   Windows: 请从官网下载安装。
3.  **Poppler:** 用于生成基于图片的视觉对照报告。
    -   macOS: `brew install poppler`
    -   Windows: 下载二进制文件并添加到 PATH。

## 安装

```bash
pip install -r requirements.txt
```

## 使用方法

### 命令行使用 (安装后)

如果你通过 pip 安装了本包，可以直接使用 `instappt` 命令：

```bash
instappt --input input.pptx --output output_dir --lang English --config model_info.json
```

### 开发模式使用

如果你是直接运行源码：

```bash
python main.py --input input.pptx --output output_dir --lang English
```

### 使用配置文件

创建一个 `model_info.json` 文件来配置 LLM 设置：

```json
{
    "translator": {
        "model": "gpt-4o",
        "api_key": "sk-...",
        "base_url": "https://api.openai.com/v1"
    }
}
```

运行命令：

```bash
python main.py --input input.pptx --output output_dir --lang English --config model_info.json
```

### 强制重新翻译 (禁用缓存)

如果你想忽略缓存并强制重新翻译：

```bash
python main.py --input input.pptx --output output_dir --lang English --config model_info.json --no-cache
```

## SDK 使用 (Python)

你也可以将 InstaPPT 作为 Python 库集成到你自己的项目中。

```python
from instappt.core import PPTTranslator
from instappt.models import SDKConfig, ModelConfig

# 1. 配置模型
config = SDKConfig(
    translator_config=ModelConfig(
        model="gpt-4o",
        api_key="sk-...",
        base_url="https://api.openai.com/v1"
    ),
    optimizer_config=ModelConfig(
        model="gpt-4o",
        api_key="sk-...",
        base_url="https://api.openai.com/v1"
    ),
    evaluator_config=ModelConfig(
        model="gpt-4o",
        api_key="sk-...",
        base_url="https://api.openai.com/v1"
    ),
    enable_cache=True # 设置为 False 可禁用缓存
)

# 2. 初始化翻译器
translator = PPTTranslator(config, concurrency=32)

# 3. 处理 PPTX
input_file = "presentation.pptx"
output_file = "presentation_translated.pptx"
target_language = "English"

translator.process_ppt(input_file, output_file, target_language)

# 4. 生成报告 (可选)
translator.generate_reports(
    output_dir="output_folder",
    report_prefix="my_report_",
    original_pptx=input_file,
    translated_pptx=output_file
)
```

## 输出文件

工具将在指定的输出目录中生成：
1.  **翻译后的 PPTX:** `[文件名]_translated.pptx`
2.  **视觉对照报告:** `[文件名]_comparison.pdf` (左右对照的图片版 PDF)
3.  **评估报告:** `[文件名]_assessment_report.pdf` (质量评分)
4.  **Token 使用统计:** `token_usage.json` (成本追踪)

## 许可证

本项目采用 GNU Affero General Public License v3.0 (AGPL-3.0) 许可证。详情请参阅 [LICENSE](LICENSE) 文件。
