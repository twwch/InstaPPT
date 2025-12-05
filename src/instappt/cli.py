import os
import sys
import argparse
import json
from instappt.core import PPTTranslator
from instappt.models import SDKConfig, ModelConfig

def main():
    parser = argparse.ArgumentParser(description="InstaPPT Translator CLI")
    parser.add_argument("--ui", action="store_true", help="Launch the Web UI")
    parser.add_argument("--input", "-i", type=str, help="Input PPTX file")
    parser.add_argument("--output", "-o", type=str, help="Output directory")
    parser.add_argument("--lang", "-l", type=str, default="Spanish", help="Target Language")
    parser.add_argument("--concurrency", "-c", type=int, default=32, help="Concurrency level (default: 32)")
    parser.add_argument("--config", type=str, help="Path to JSON configuration file")
    parser.add_argument("--no-cache", action="store_true", help="Disable LLM caching")
    
    args = parser.parse_args()
    
    if args.ui:
        from instappt.ui import launch_ui
        print("Launching Web UI...")
        launch_ui()
        return

    # Validate required args for CLI mode
    if not args.input or not args.output:
        parser.error("the following arguments are required: --input/-i, --output/-o (unless --ui is used)")
    
    translator_cfg = None
    evaluator_cfg = None
    optimizer_cfg = None
    
    if args.config and os.path.exists(args.config):
        try:
            with open(args.config, 'r') as f:
                config_data = json.load(f)
            
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
        except Exception as e:
            print(f"Error loading config file: {e}")
            return

    # Fallback / Default logic
    default_key = os.getenv("OPENAI_API_KEY")
    default_base = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    default_model = "gpt-3.5-turbo"
    
    if not translator_cfg:
        if not default_key:
             print("Error: No config file and OPENAI_API_KEY invalid. Please provide --config or set env vars.")
             return
        common = ModelConfig(api_key=default_key, base_url=default_base, model=default_model)
        translator_cfg = evaluator_cfg = optimizer_cfg = common
    else:
        if not evaluator_cfg: evaluator_cfg = translator_cfg
        if not optimizer_cfg: optimizer_cfg = translator_cfg

    sdk_config = SDKConfig(
        translator_config=translator_cfg,
        optimizer_config=optimizer_cfg,
        evaluator_config=evaluator_cfg,
        enable_cache=not args.no_cache
    )
    
    translator = PPTTranslator(sdk_config, concurrency=args.concurrency)
    
    # Output is a directory
    output_root = args.output
    
    if os.path.exists(output_root) and not os.path.isdir(output_root):
        print(f"Error: Output path '{output_root}' exists as a file. Please remove it or specify a different directory.")
        return

    if not os.path.exists(output_root):
        os.makedirs(output_root)
        
    input_filename = os.path.basename(args.input)
    output_pptx_name = input_filename.replace(".pptx", "_translated.pptx")
    output_pptx_path = os.path.join(output_root, output_pptx_name)
    reports_dir = output_root
    
    print(f"Starting translation of {args.input} to {args.lang} with concurrency {args.concurrency}...")
    translator.process_ppt(args.input, output_pptx_path, args.lang)
    
    input_filename_no_ext = input_filename.replace(".pptx", "")
    print("Generating reports...")
    translator.generate_reports(
        reports_dir, 
        report_prefix=input_filename_no_ext + "_",
        original_pptx=args.input,
        translated_pptx=output_pptx_path
    )
    print(f"Done! Output saved to {output_pptx_path} and reports in {reports_dir}")

if __name__ == "__main__":
    main()
