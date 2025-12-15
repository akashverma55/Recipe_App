from flask import Flask, request, jsonify
from flask_cors import CORS
from pydantic import BaseModel, ValidationError, Field
from typing import List, Optional
from recipe_generator import RecipeGenerator
from config import Config
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for Flutter app to communicate

# Validate configuration
Config.validate()

# Initialize Recipe Generator
recipe_generator = RecipeGenerator()

# Pydantic models for request validation
class RecipeRequest(BaseModel):
    ingredients: List[str] = Field(..., min_length=1, max_length=Config.MAX_INGREDIENTS)
    cuisine_type: Optional[str] = None
    dietary_restrictions: Optional[List[str]] = []

class MultipleRecipesRequest(BaseModel):
    ingredients: List[str] = Field(..., min_length=1, max_length=Config.MAX_INGREDIENTS)
    count: int = Field(default=3, ge=1, le=5)

# Root endpoint
@app.route('/', methods=['GET'])
def home():
    """Health check endpoint"""
    return jsonify({
        "message": "Recipe Generator API is running",
        "version": "1.0.0",
        "endpoints": {
            "/generate_recipe": "POST - Generate a single detailed recipe",
            "/suggest_recipes": "POST - Get multiple recipe suggestions",
            "/health": "GET - Health check"
        }
    }), 200

# Health check endpoint
@app.route('/health', methods=['GET'])
def health():
    """Check if the API is healthy"""
    return jsonify({"status": "healthy", "message": "API is running"}), 200

# Generate single recipe endpoint
@app.route('/generate_recipe', methods=['POST'])
def generate_recipe():
    """
    Generate a detailed recipe based on ingredients
    
    Expected JSON body:
    {
        "ingredients": ["chicken", "tomato", "onion"],
        "cuisine_type": "Italian",  // Optional
        "dietary_restrictions": ["gluten-free"]  // Optional
    }
    """
    try:
        # Get JSON data
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "error": "No data provided"
            }), 400
        
        # Validate request using Pydantic
        try:
            recipe_request = RecipeRequest(**data)
        except ValidationError as e:
            return jsonify({
                "success": False,
                "error": "Validation error",
                "details": e.errors()
            }), 400
        
        # Log request
        logger.info(f"Generating recipe with ingredients: {recipe_request.ingredients}")
        
        # Generate recipe
        result = recipe_generator.generate_recipe(
            ingredients=recipe_request.ingredients,
            cuisine_type=recipe_request.cuisine_type,
            dietary_restrictions=recipe_request.dietary_restrictions
        )
        
        if result["success"]:
            logger.info(f"Recipe generated successfully: {result['recipe'].get('recipe_name', 'Unknown')}")
            return jsonify(result), 200
        else:
            logger.error(f"Recipe generation failed: {result.get('error', 'Unknown error')}")
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Internal server error",
            "message": str(e)
        }), 500

# Suggest multiple recipes endpoint
@app.route('/suggest_recipes', methods=['POST'])
def suggest_recipes():
    """
    Get multiple recipe suggestions based on ingredients
    
    Expected JSON body:
    {
        "ingredients": ["chicken", "rice", "vegetables"],
        "count": 3  // Optional, default is 3
    }
    """
    try:
        # Get JSON data
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "error": "No data provided"
            }), 400
        
        # Validate request
        try:
            recipes_request = MultipleRecipesRequest(**data)
        except ValidationError as e:
            return jsonify({
                "success": False,
                "error": "Validation error",
                "details": e.errors()
            }), 400
        
        # Log request
        logger.info(f"Suggesting {recipes_request.count} recipes with ingredients: {recipes_request.ingredients}")
        
        # Generate multiple recipes
        result = recipe_generator.generate_multiple_recipes(
            ingredients=recipes_request.ingredients,
            count=recipes_request.count
        )
        
        if result["success"]:
            logger.info(f"Generated {len(result.get('recipes', []))} recipe suggestions")
            return jsonify(result), 200
        else:
            logger.error(f"Recipe suggestion failed: {result.get('error', 'Unknown error')}")
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Internal server error",
            "message": str(e)
        }), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": "Endpoint not found",
        "message": "The requested endpoint does not exist"
    }), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        "success": False,
        "error": "Method not allowed",
        "message": "The HTTP method is not allowed for this endpoint"
    }), 405

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "success": False,
        "error": "Internal server error",
        "message": "An unexpected error occurred"
    }), 500

# Run the application
if __name__ == '__main__':
    logger.info("Starting Recipe Generator API...")
    logger.info(f"Server running on {Config.HOST}:{Config.PORT}")
    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG
    )