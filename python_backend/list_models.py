import google.generativeai as genai
from config import Config

# Configure API
genai.configure(api_key=Config.GEMINI_API_KEY)

print("Available Gemini Models:")
print("=" * 60)

for model in genai.list_models():
    if 'generateContent' in model.supported_generation_methods:
        print(f"\n✅ {model.name}")
        print(f"   Display Name: {model.display_name}")
        print(f"   Description: {model.description}")
        print(f"   Methods: {', '.join(model.supported_generation_methods)}")

print("\n" + "=" * 60)
print("\nRecommended for your project: gemini-1.5-flash")
print("Update your .env file: GEMINI_MODEL=gemini-1.5-flash")