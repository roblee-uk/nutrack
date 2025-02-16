import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime

# Initialize Supabase client
url: str = st.secrets["supabase"]["SUPABASE_URL"]
key: str = st.secrets["supabase"]["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# ----------------------------------------------------------- #
# Define Functions used in page ----------------------------- #
# ----------------------------------------------------------- #

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

# Function to populate a dataframe of all foods
def fetch_food_data():
    response = supabase.table("foods").select("*").execute()
    df = pd.DataFrame(response.data)
    return df

# Preload data using functions defined (where appropriate)
recipes = fetch_recipe_data()
foods = fetch_food_data()

# ---------------------------------------------------- #
# Saved Recipes -------------------------------------- #
# ---------------------------------------------------- #

# Display recipe data
# Allowing the user to select a single row at a time
st.title("Saved Recipes")
recipe_selection = st.dataframe(recipes['recipe_name']
                                , hide_index=True
                                , on_select="rerun"
                                , selection_mode="single-row")

# When a selection is made using the st.dataframe above
# Save the recipe_id it to a variable that can be called later on
selected_recipe = recipes['recipe_id'].iloc[recipe_selection['selection']['rows']]

# If a selection has been made show the foods which make up the recipe selected
if len(selected_recipe) > 0:
    id = selected_recipe.loc[0]
    st.dataframe(fetch_recipe_ingredients(id), hide_index=True)

    # Form for adding food to recipe
    st.subheader("Add New Food to Recipe")
    with st.form("new_food_form", clear_on_submit=True,):
        food_name = st.selectbox("Food Name", options=foods['food_name'])
        amount = st.number_input("Amount (g)", min_value=0.0, step=0.1)
        
        
        st.write(food_name)
        submitted = st.form_submit_button("Add Food")

        food_id = foods[foods['food_name']==food_name]['food_id'].to_list()[0]
        st.write(selected_recipe.to_list()[0])
        
        if submitted:
            new_ingredient = {
                "food_id": food_id,
                "recipe_id": selected_recipe.to_list()[0],
                "amount": amount
                }
            
            response = supabase.table("recipe_ingredients").insert(new_ingredient).execute()
            
            if response.data:
                st.success(f"Successfully added {food_name} to the ingredients for {recipes[recipes['recipe_id']==selected_recipe]}!")
                st.rerun()
            else:
                st.error("Failed to add food to the database. Please try again.")

#st.dataframe(selected_ingredients[selected_ingredients['recipe_id']==selected_recipe])





