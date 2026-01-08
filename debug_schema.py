import sys
import os
import json
sys.path.insert(0, os.path.abspath("src"))

from instappt.models import SDKConfig

try:
    schema = SDKConfig.model_json_schema()
    print(json.dumps(schema, indent=2))
except Exception as e:
    print(f"Error generating schema: {e}")
