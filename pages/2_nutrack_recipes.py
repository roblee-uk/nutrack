import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime

# Initialize Supabase client
url: str = st.secrets["supabase"]["SUPABASE_URL"]
key: str = st.secrets["supabase"]["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# Function to fetch and display data
def fetch_recipe_data():
    response = supabase.table("recipes").select("*").execute()
    df = pd.DataFrame(response.data)
    return df

# Function to fetch and display data
def fetch_recipe_ingredients(recipe_id):
    response = supabase.table("recipe_ingredients").select('*, foods(*)').execute()
    df = pd.DataFrame(response.data)

    food_cols = ['food_id', 'food_name', 'protein', 'carbohydrates', 'sugars', 'fat', 'saturates', 'fiber'] 
    foods_expanded = pd.json_normalize(df['foods'])[food_cols]
    
    recipe_cols = ['recipe_id', 'food_id', 'amount']
    df = df[recipe_cols]
    
    clean_df = pd.merge(df, foods_expanded, on='food_id')

    for col in food_cols[2:]:
        clean_df[col] = clean_df.apply(lambda row: row[col] * (row['amount']/100), axis=1)

    display_cols = ['food_name', 'amount', 'protein', 'carbohydrates', 'sugars', 'fat', 'saturates', 'fiber']

    return clean_df[clean_df['recipe_id']==recipe_id][display_cols]

recipes = fetch_recipe_data()

# Display existing data
st.title("Saved Recipes")
recipe_selection = st.dataframe(recipes['recipe_name']
                                , hide_index=True
                                , on_select="rerun"
                                , selection_mode="single-row")

selected_recipe = recipes['recipe_id'].iloc[recipe_selection['selection']['rows']]

if len(selected_recipe) > 0:
    id = selected_recipe.loc[0]
    st.dataframe(fetch_recipe_ingredients(id), hide_index=True)

#st.dataframe(selected_ingredients[selected_ingredients['recipe_id']==selected_recipe])





""" # Form for new food entry
st.subheader("Add New Food")
with st.form("new_food_form", clear_on_submit=True,):
    name = st.text_input("Food Name")
    protein = st.number_input("Protein Content (g)", min_value=0.0, step=0.1)
    carbs = st.number_input("Carbohydrate Content (g)", min_value=0.0, step=0.1)
    sugars = st.number_input("of which sugars (g)", min_value=0.0, step=0.1)
    fat = st.number_input("Fat Content (g)", min_value=0.0, step=0.1)
    sats = st.number_input("of which saturates (g)", min_value=0.0, step=0.1)
    fiber = st.number_input("Fiber Content (g)", min_value=0.0, step=0.1)
    
    submitted = st.form_submit_button("Add Food")
    
    if submitted:
        current_time = datetime.now().isoformat()
        new_food = {
            "food_name": name,
            "protein": protein,
            "carbohydrates": carbs,
            "sugars": sugars,
            "fat": fat,
            "saturates": sats,
            "fiber": fiber,
            "created_at": current_time,
            "updated_at": current_time
        }
        
        response = supabase.table("foods").insert(new_food).execute()
        
        if response.data:
            st.success(f"Successfully added {name} to the database!")
            st.rerun()
        else:
            st.error("Failed to add food to the database. Please try again.") """