import json

def describe_json(data, indent=0):
    pad = '  ' * indent
    if isinstance(data, dict):
        for key, value in data.items():
            print(f"{pad}{key}: {type(value).__name__}")
            describe_json(value, indent + 1)
    elif isinstance(data, list):
        print(f"{pad}List[{len(data)}] of {type(data[0]).__name__}" if data else f"{pad}Empty List")
        if data:
            describe_json(data[0], indent + 1)
    else:
        print(f"{pad}{type(data).__name__}")

# Load and analyze JSON
with open('data/main.json', 'r') as f:
    data = json.load(f)
    describe_json(data)
