import pickle

# Check what's inside the model.pkl file
try:
    with open("model.pkl", "rb") as f:
        model_data = pickle.load(f)
    
    print("Model loaded successfully!")
    print(f"Type of loaded data: {type(model_data)}")
    
    if isinstance(model_data, tuple):
        print(f"Number of items in tuple: {len(model_data)}")
        for i, item in enumerate(model_data):
            print(f"Item {i}: {type(item)}")
    
except Exception as e:
    print(f"Error loading model: {e}")
