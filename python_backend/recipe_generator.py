import google.generativeai as genai
from typing import List, Dict, Optional
import json
import re
from config import Config

class RecipeGenerator:
    """Handles recipe generation using Google's Gemini AI"""
    
    def __init__(self):
        """Initialize the Gemini model"""
        genai.configure(api_key=Config.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(Config.GEMINI_MODEL)
        
    def generate_recipe(self, ingredients: List[str], cuisine_type: Optional[str] = None, 
                       dietary_restrictions: Optional[List[str]] = None) -> Dict:
        """
        Generate a recipe based on provided ingredients
        
        Args:
            ingredients: List of available ingredients
            cuisine_type: Optional cuisine preference (e.g., Italian, Indian, Chinese)
            dietary_restrictions: Optional list of dietary restrictions (e.g., vegetarian, vegan, gluten-free)
            
        Returns:
            Dictionary containing recipe details
        """
        try:
            # Build the prompt
            prompt = self._build_prompt(ingredients, cuisine_type, dietary_restrictions)
            
            # Generate content
            response = self.model.generate_content(prompt)
            
            # Parse the response
            recipe_data = self._parse_response(response.text)
            
            return {
                "success": True,
                "recipe": recipe_data
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to generate recipe"
            }
    
    def _build_prompt(self, ingredients: List[str], cuisine_type: Optional[str], 
                     dietary_restrictions: Optional[List[str]]) -> str:
        """Build a detailed prompt for the AI model"""
        
        ingredients_str = ", ".join(ingredients)
        
        prompt = f"""You are a professional chef. Create a detailed recipe using the following ingredients: {ingredients_str}

Instructions:
1. Create ONE complete recipe that uses as many of the provided ingredients as possible
2. You can suggest common pantry items (salt, pepper, oil, etc.) if needed
3. Provide the response in the following JSON format ONLY (no additional text):

{{
  "recipe_name": "Name of the dish",
  "description": "Brief description of the dish",
  "cuisine_type": "Type of cuisine",
  "prep_time": "Preparation time in minutes",
  "cook_time": "Cooking time in minutes",
  "servings": "Number of servings",
  "difficulty": "Easy/Medium/Hard",
  "ingredients": [
    {{"item": "ingredient name", "quantity": "amount", "unit": "measurement unit"}}
  ],
  "instructions": [
    "Step 1 instruction",
    "Step 2 instruction"
  ],
  "nutritional_info": {{
    "calories": "approximate calories per serving",
    "protein": "grams",
    "carbs": "grams",
    "fat": "grams"
  }},
  "tips": [
    "Cooking tip 1",
    "Cooking tip 2"
  ]
}}
"""
        
        # Add cuisine preference if provided
        if cuisine_type:
            prompt += f"\n- Prefer {cuisine_type} cuisine style"
        
        # Add dietary restrictions if provided
        if dietary_restrictions and len(dietary_restrictions) > 0:
            restrictions_str = ", ".join(dietary_restrictions)
            prompt += f"\n- Follow these dietary restrictions: {restrictions_str}"
        
        prompt += "\n\nProvide ONLY the JSON response, no additional text or markdown formatting."
        
        return prompt
    
    def _parse_response(self, response_text: str) -> Dict:
        """Parse the AI response and extract recipe data"""
        try:
            # Remove markdown code blocks if present
            cleaned_text = response_text.strip()
            if cleaned_text.startswith("```"):
                # Remove ```json or ``` at start and ``` at end
                cleaned_text = re.sub(r'^```(?:json)?\s*', '', cleaned_text)
                cleaned_text = re.sub(r'\s*```$', '', cleaned_text)
            
            # Parse JSON
            recipe_data = json.loads(cleaned_text.strip())
            
            # Validate required fields
            required_fields = ["recipe_name", "ingredients", "instructions"]
            for field in required_fields:
                if field not in recipe_data:
                    raise ValueError(f"Missing required field: {field}")
            
            return recipe_data
            
        except json.JSONDecodeError as e:
            # If JSON parsing fails, return a fallback structure
            return {
                "recipe_name": "Generated Recipe",
                "description": response_text[:200],
                "ingredients": [],
                "instructions": [response_text],
                "error": "Failed to parse structured recipe"
            }
        except Exception as e:
            raise Exception(f"Error parsing recipe: {str(e)}")
    
    def generate_multiple_recipes(self, ingredients: List[str], count: int = 3) -> Dict:
        """Generate multiple recipe suggestions"""
        try:
            prompt = f"""You are a professional chef. Suggest {count} different recipes using these ingredients: {", ".join(ingredients)}

Provide {count} brief recipe ideas in JSON format:
{{
  "recipes": [
    {{
      "recipe_name": "Name",
      "description": "Brief description",
      "cuisine_type": "Type",
      "difficulty": "Easy/Medium/Hard",
      "estimated_time": "Total time in minutes"
    }}
  ]
}}

Provide ONLY the JSON response."""
            
            response = self.model.generate_content(prompt)
            
            # Parse response
            cleaned_text = response.text.strip()
            if cleaned_text.startswith("```"):
                cleaned_text = re.sub(r'^```(?:json)?\s*', '', cleaned_text)
                cleaned_text = re.sub(r'\s*```$', '', cleaned_text)
            
            recipes_data = json.loads(cleaned_text.strip())
            
            return {
                "success": True,
                "recipes": recipes_data.get("recipes", [])
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to generate recipe suggestions"
            }