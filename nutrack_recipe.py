import streamlit as st
import pandas as pd
from supabase import create_client, Client

# Initialize Supabase client using Streamlit secrets
url: str = st.secrets["supabase"]["SUPABASE_URL"]
key: str = st.secrets["supabase"]["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# Function to fetch recipes
def fetch_recipes():
    response = supabase.table("recipes").select("*").execute()
    return response.data

# Function to fetch foods
def fetch_foods():
    response = supabase.table("foods").select("food_id, food_name").execute()
    return response.data

# Function to add a new recipe
def add_recipe(recipe_name, directions):
    response = supabase.table("recipes").insert({"recipe_name": recipe_name, "directions": directions}).execute()
    return response.data[0]["recipe_id"]

# Function to add an ingredient to a recipe
def add_ingredient(recipe_id, food_id, amount):
    supabase.table("recipe_ingredients").insert({
        "recipe_id": recipe_id,
        "food_id": food_id,
        "amount": amount
    }).execute()

# Function to fetch ingredients for a specific recipe
def fetch_ingredients(recipe_id):
    query = f"""
    SELECT 
        f.food_name, 
        ri.amount AS "Amount (grams)", 
        f.protein, 
        f.carbohydrates, 
        f.sugars, 
        f.fats, 
        f.saturates, 
        f.fiber
    FROM 
        recipe_ingredients ri
    JOIN 
        foods f ON ri.food_id = f.food_id
    WHERE 
        ri.recipe_id = {recipe_id}
    """
    response = supabase.rpc('get_recipe_ingredients', {'recipe_id': recipe_id}).execute()
    return response.data

# Main app
st.title("Recipe Manager")

# Fetch all recipes
recipes = fetch_recipes()

if recipes:
    st.write("### All Recipes")
    
    # Convert recipes into a DataFrame for display
    recipes_df = pd.DataFrame(recipes)
    
    # Display the recipes table with checkboxes
    selected_recipe = st.selectbox("Select a Recipe", options=recipes_df['recipe_name'], key='recipe_selector')
    
    if selected_recipe:
        recipe_id = recipes_df[recipes_df['recipe_name'] == selected_recipe]['recipe_id'].values[0]
        st.write(f"### Ingredients for: {selected_recipe}")
        ingredients = fetch_ingredients(recipe_id)
        if ingredients:
            ingredients_df = pd.DataFrame(ingredients)
            st.table(ingredients_df)
        else:
            st.write("No ingredients found for this recipe.")

# Collapsible form for adding a new recipe
with st.expander("Add New Recipe"):
    new_recipe_name = st.text_input("Recipe Name")
    new_recipe_directions = st.text_area("Directions")
    
    if st.button("Add Recipe"):
        if new_recipe_name and new_recipe_directions:
            new_recipe_id = add_recipe(new_recipe_name, new_recipe_directions)
            st.success(f"Recipe added successfully! Recipe ID: {new_recipe_id}")
            st.session_state.new_recipe_id = new_recipe_id
            st.session_state.show_ingredient_form = True
        else:
            st.error("Please fill in both recipe name and directions.")

# Form for adding ingredients to the new recipe
if st.session_state.get('show_ingredient_form', False):
    with st.expander("Add Ingredients to New Recipe", expanded=True):
        foods = fetch_foods()
        if foods:
            food_options = {f["food_name"]: f["food_id"] for f in foods}
            selected_food = st.selectbox("Select Food", list(food_options.keys()))
            amount = st.number_input("Amount (grams)", min_value=0.1, step=0.1)
            
            if st.button("Add Ingredient"):
                add_ingredient(st.session_state.new_recipe_id, food_options[selected_food], amount)
                st.success(f"Ingredient added successfully to Recipe ID: {st.session_state.new_recipe_id}")

# Reset the app state for starting a new recipe entry process
if st.button("Start New Recipe"):
    st.session_state.pop('new_recipe_id', None)
    st.session_state.pop('show_ingredient_form', None)
    st.rerun()
