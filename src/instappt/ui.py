import gradio as gr
import os
import json
import shutil
import pandas as pd
from instappt.core import PPTTranslator
from instappt.models import SDKConfig, ModelConfig

def parse_markdown_glossary(text):
    if not text or not text.strip():
        return None, "Empty glossary"
    
    try:
        lines = [line.strip() for line in text.strip().split('\n') if line.strip()]
        if not lines:
            return None, "Empty glossary"

        # Find header
        header_line = lines[0]
        if "|" not in header_line:
             return None, "No valid markdown table header found."
             
        headers = [h.strip() for h in header_line.split('|') if h.strip()]
        
        data = []
        start_idx = 1
        
        # Check/Skip separator
        if len(lines) > 1 and "---" in lines[1]:
            start_idx = 2
            
        for line in lines[start_idx:]:
            if "|" not in line: continue
            # Handle escaped pipes? Assuming simple for now
            row = [c.strip() for c in line.split('|') if c.strip()]
            
            # Pad or truncate to match headers length
            if len(row) < len(headers):
                row += [""] * (len(headers) - len(row))
            elif len(row) > len(headers):
                row = row[:len(headers)]
                
            data.append(row)
            
        df = pd.DataFrame(data, columns=headers)
        return df, f"Successfully parsed {len(data)} terms."
    except Exception as e:
        return None, f"Error parsing glossary: {str(e)}"

def translate_ppt(file, lang, config_json, use_cache, glossary_text, progress=gr.Progress()):
    if not file:
        raise gr.Error("Please upload a PPTX file.")
    
    # 1. Parse Config
    try:
        config_data = json.loads(config_json)
    except json.JSONDecodeError:
        raise gr.Error("Invalid JSON configuration.")

    def load_from_json(key):
        if key not in config_data: return None
        return ModelConfig(
            model=config_data[key].get("model", "gpt-3.5-turbo"),
            api_key=config_data[key].get("api_key", os.getenv("OPENAI_API_KEY", "")),
            base_url=config_data[key].get("base_url", os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"))
        )

    translator_cfg = load_from_json("translator")
    evaluator_cfg = load_from_json("evaluator")
    optimizer_cfg = load_from_json("optimizer")
    
    # Defaults
    default_key = os.getenv("OPENAI_API_KEY")
    default_base = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    default_model = "gpt-3.5-turbo"
    
    if not translator_cfg:
        if not default_key:
             raise gr.Error("No API Key provided in config or env vars.")
        common = ModelConfig(api_key=default_key, base_url=default_base, model=default_model)
        translator_cfg = evaluator_cfg = optimizer_cfg = common
    else:
        if not evaluator_cfg: evaluator_cfg = translator_cfg
        if not optimizer_cfg: optimizer_cfg = translator_cfg

    sdk_config = SDKConfig(
        translator_config=translator_cfg,
        optimizer_config=optimizer_cfg,
        evaluator_config=evaluator_cfg,
        enable_cache=use_cache
    )
    
    translator = PPTTranslator(sdk_config, concurrency=32) # Lower concurrency for web app safety
    
    # 2. Setup Paths
    # Gradio stores uploaded file in a temp path
    input_path = file.name
    input_filename = os.path.basename(input_path)
    
    # Create a unique output directory
    output_root = os.path.join("output_gradio", os.path.splitext(input_filename)[0])
    if os.path.exists(output_root):
        shutil.rmtree(output_root)
    os.makedirs(output_root)
    
    output_pptx_name = input_filename.replace(".pptx", "_translated.pptx")
    output_pptx_path = os.path.join(output_root, output_pptx_name)
    
    # 3. Process with Progress
    # progress(0, desc="Starting...")
    
    last_update_val = -1.0
    
    def progress_callback(current, total, stage_name):
        nonlocal last_update_val
        # Map stages to progress range [0, 1]
        # Translation: 0-0.4
        # Evaluation: 0.4-0.7
        # Optimization: 0.7-1.0
        
        base = 0.0
        scale = 0.4
        if stage_name == "Evaluation":
            base = 0.4
            scale = 0.3
        elif stage_name == "Optimization":
            base = 0.7
            scale = 0.3
            
        fraction = current / total if total > 0 else 0
        overall = base + (fraction * scale)
        
        # Throttle: only update if changed by > 0.01 (1%)
        if abs(overall - last_update_val) > 0.01 or current == total:
            # print(f"DEBUG: Updating UI Progress: {overall:.2f}")
            try:
                progress(overall, desc=f"{stage_name} ({current}/{total})")
                last_update_val = overall
            except Exception as e:
                print(f"DEBUG: Gradio progress update failed: {e}")

    try:
        translator.process_ppt(input_path, output_pptx_path, lang, glossary_content=glossary_text, progress_callback=progress_callback)
    except Exception as e:
        raise gr.Error(f"Translation failed: {str(e)}")
        
    # 4. Generate Reports
    progress(0.95, desc="Generating Reports...")
    input_filename_no_ext = os.path.splitext(input_filename)[0]
    
    try:
        translator.generate_reports(
            output_root, 
            report_prefix=input_filename_no_ext + "_",
            original_pptx=input_path,
            translated_pptx=output_pptx_path
        )
    except Exception as e:
        print(f"Report generation warning: {e}")

    # 5. Collect Files
    output_files = []
    for root, dirs, files in os.walk(output_root):
        for f in files:
            if not f.startswith("."):
                output_files.append(os.path.join(root, f))
                
    return output_files

def create_ui():
    default_config = {
        "translator": {
            "model": "gpt-4o",
            "api_key": "",
            "base_url": "https://api.openai.com/v1"
        },
        "evaluator": {
            "model": "gpt-4o",
            "api_key": "",
            "base_url": "https://api.openai.com/v1"
        },
        "optimizer": {
            "model": "gpt-4o",
            "api_key": "",
            "base_url": "https://api.openai.com/v1"
        }
    }

    with gr.Blocks(title="InstaPPT Translator") as app:
        gr.Markdown("# InstaPPT AI Translator")
        
        with gr.Row():
            with gr.Column():
                file_input = gr.File(label="Upload PPTX", file_types=[".pptx"])
                languages = ["English", "Chinese", "Spanish", "French", "German", "Japanese", "Korean", "Russian", "Arabic", "Portuguese", "Italian"]
                lang_input = gr.Dropdown(label="Target Language", choices=languages, value="English", allow_custom_value=True)
                cache_input = gr.Checkbox(label="Enable Cache", value=True)
                
                gr.Markdown("### Terminology Glossary")
                with gr.Row():
                    glossary_input = gr.TextArea(label="Markdown Table", placeholder="| Term | Translation |\n| --- | --- |\n| AI | 人工智能 |", lines=5)
                with gr.Row():
                    validate_btn = gr.Button("Validate Glossary", size="sm")
                    glossary_status = gr.Markdown("")
                
                glossary_preview = gr.Dataframe(label="Glossary Preview", interactive=False, wrap=True)
                
                def on_validate(text):
                    df, msg = parse_markdown_glossary(text)
                    if df is not None:
                        return df, f"✅ {msg}"
                    return None, f"❌ {msg}"

                validate_btn.click(on_validate, inputs=[glossary_input], outputs=[glossary_preview, glossary_status])

                config_input = gr.Code(label="Model Configuration (JSON)", value=json.dumps(default_config, indent=4), language="json")
                submit_btn = gr.Button("Start Translation", variant="primary")
            
            with gr.Column():
                output_files = gr.File(label="Download Results", file_count="multiple")
        
        submit_btn.click(
            fn=translate_ppt,
            inputs=[file_input, lang_input, config_input, cache_input, glossary_input],
            outputs=[output_files]
        )
    return app

def launch_ui(server_name="0.0.0.0", server_port=7860):
    app = create_ui()
    app.launch(server_name=server_name, server_port=server_port)
