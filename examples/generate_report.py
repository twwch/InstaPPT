import os
import sys
import json
import re
from typing import List, Dict
import time
from tqdm import tqdm

# Add src to path to import local modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from instappt.prompts import EVALUATION_PROMPT

# Try to import openai
try:
    from openai import OpenAI
except ImportError:
    print("Please install openai: pip install openai")
    sys.exit(1)

def parse_markdown_table(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    data = []
    # Simple parser for the specific format in merged.md
    # Expecting: | 序号 | 中文 (V0) | English (V1) |
    
    start_parsing = False
    for line in lines:
        line = line.strip()
        if not line: continue
        
        if "| 序号 |" in line:
            start_parsing = True
            continue
        if "---" in line:
            continue
            
        if start_parsing and line.startswith("|") and line.endswith("|"):
            parts = line.split("|")
            # Parts indices: 0="", 1=序号, 2=中文, 3=English, 4=""
            if len(parts) >= 5:
                # Replace <br> with newlines for better readability in prompt
                source = parts[2].strip().replace("<br>", "\n")
                target = parts[3].strip().replace("<br>", "\n")
                if source and target:
                    data.append({"source": source, "target": target})
    return data

def evaluate_segment(client, source, target, model="gpt-4o"):
    prompt = EVALUATION_PROMPT.format(
        source_text=source,
        target_language="English", # Assuming V1 is English based on file header
        translation=target,
        glossary="" # No glossary for this batch report for now
    )
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.3
        )
        content = response.choices[0].message.content
        return json.loads(content)
    except Exception as e:
        print(f"Error evaluating segment: {e}")
        return None

def generate_report(results, output_file):
    avg_scores = {k: 0.0 for k in ["accuracy", "fluency", "consistency", "terminology", "completeness"]}
    count = 0
    final_score_sum = 0
    
    report_lines = []
    report_lines.append("# Translation Quality Assessment Report\n")
    report_lines.append(f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    report_lines.append("## 1. Executive Summary\n")
    
    details = []
    
    for i, res in enumerate(results):
        if not res: continue
        metrics = res.get("metrics", {})
        overall = res.get("overall_score", 0)
        suggestions = res.get("suggestions", "")
        
        count += 1
        final_score_sum += overall
        for k in avg_scores:
            avg_scores[k] += metrics.get(k, 0)
            
        # Collect low scores or just all details? User wants a report.
        # Let's list items with suggestions or score < 10
        if overall < 9.0 or suggestions:
            details.append(f"### Segment {i+1}")
            details.append(f"- **Overall Score:** {overall}")
            details.append(f"- **Metrics:** {json.dumps(metrics)}")
            if suggestions:
                details.append(f"- **Suggestions:** {suggestions}")
            details.append("\n")
            
    if count > 0:
        for k in avg_scores:
            avg_scores[k] /= count
        final_avg = final_score_sum / count
        
        report_lines.append(f"**Overall Quality Score:** {final_avg:.2f} / 10\n")
        report_lines.append("| Metric | Average Score |")
        report_lines.append("| :--- | :--- |")
        for k, v in avg_scores.items():
            report_lines.append(f"| {k.capitalize()} | {v:.2f} |")
        report_lines.append("\n")
    else:
        report_lines.append("No valid evaluation results obtained.\n")
        
    report_lines.append("## 2. Issues & Suggestions\n")
    if details:
        report_lines.extend(details)
    else:
        report_lines.append("No specific issues found. Translation quality is high.\n")
        
    with open(output_file, 'w', encoding='utf-8') as f:
        f.writelines([l + "\n" for l in report_lines])
    
    print(f"Report generated: {output_file}")

def main():
    input_file = os.path.join(os.path.dirname(__file__), "merged.md")
    output_file = os.path.join(os.path.dirname(__file__), "evaluation_report.md")
    
    # Check API Key
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    
    # Load from model_info.json if available
    config_path = os.path.join(os.path.dirname(__file__), "..", "model_info.json")
    config = {}
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                # Check translator config first
                if "translator" in config:
                    api_key = config["translator"].get("api_key", api_key)
                    base_url = config["translator"].get("base_url", base_url)
        except Exception as e:
            print(f"Error loading config: {e}")

    if not api_key:
        print("Error: OPENAI_API_KEY not set and not found in model_info.json")
        return

    # Determine Model Name
    model_name = "gpt-4o"
    if "translator" in config:
        model_name = config["translator"].get("model", "gpt-4o")

    print(f"Using Model: {model_name}")
    client = OpenAI(api_key=api_key, base_url=base_url)
    
    print(f"Parsing {input_file}...")
    segments = parse_markdown_table(input_file)
    print(f"Found {len(segments)} segments.")
    
    from concurrent.futures import ThreadPoolExecutor, as_completed

    results = [None] * len(segments)
    print("Starting evaluation with concurrency=10...")
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_idx = {
            executor.submit(evaluate_segment, client, seg["source"], seg["target"], model=model_name): i
            for i, seg in enumerate(segments)
        }
        
        for future in tqdm(as_completed(future_to_idx), total=len(segments)):
            idx = future_to_idx[future]
            try:
                res = future.result()
                results[idx] = res
            except Exception as e:
                print(f"Error processing segment {idx}: {e}")
        
    # Filter out potential None results if needed, though generate_report handles None
    results = [r for r in results if r is not None]
        
    generate_report(results, output_file)

if __name__ == "__main__":
    main()
