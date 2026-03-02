from genson import SchemaBuilder
import json

with open('data/main.json') as f:
    builder = SchemaBuilder()
    builder.add_object(json.load(f))
    print(json.dumps(builder.to_schema(), indent=2))
