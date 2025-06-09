import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime
from nutrack_utils import show_sidebar_user_info, check_auth_and_profile

show_sidebar_user_info()
check_auth_and_profile()

# --- Supabase Client Initialization ---
url: str = st.secrets["supabase"]["SUPABASE_URL"]
key: str = st.secrets["supabase"]["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

def set_supabase_auth():
    supabase.postgrest.auth(st.session_state.session.access_token)

def fetch_recipe_data():
    set_supabase_auth()
    response = supabase.table("recipes").select("*").execute()
    df = pd.DataFrame(response.data)
    return df

def fetch_recipe_ingredients(recipe_id):
    set_supabase_auth()
    response = supabase.table("recipe_ingredients").select('*, foods(*)').execute()
    df = pd.DataFrame(response.data)
    if len(df) < 1:
        return df
    df = df[df['recipe_id'] == recipe_id]
    if len(df) < 1:
        return df
    else:
        food_cols = ['food_id', 'food_name', 'protein', 'carbohydrates', 'sugars', 'fat', 'saturates', 'fiber'] 
        foods_expanded = pd.json_normalize(df['foods'])[food_cols]
        recipe_cols = ['recipe_id', 'food_id', 'amount']
        df = df[recipe_cols]
        clean_df = pd.merge(df, foods_expanded, on='food_id')
        for col in food_cols[2:]:
            clean_df[col] = clean_df.apply(lambda row: row[col] * (row['amount']/100), axis=1)
        display_cols = ['food_name', 'amount', 'protein', 'carbohydrates', 'sugars', 'fat', 'saturates', 'fiber']
        return clean_df[display_cols]

def fetch_food_data():
    set_supabase_auth()
    response = supabase.table("foods").select("*").execute()
    df = pd.DataFrame(response.data)
    return df

recipes = fetch_recipe_data()
foods = fetch_food_data()

st.title("Recipes")
st.subheader("Current Saved Recipes", divider="blue")

if recipes.empty:
    st.info("No recipes yet. Add your first recipe below!")
    st.subheader("Add New Recipe", divider='blue')
    with st.form("new_recipe_form", clear_on_submit=True):
        recipe_name = st.text_input("Recipe Name")
        submitted = st.form_submit_button("Add Recipe")
        if submitted:
            set_supabase_auth()
            current_time = datetime.now().isoformat()
            new_recipe = {
                "recipe_name": recipe_name,
                "created_at": current_time,
                "updated_at": current_time
            }
            response = supabase.table("recipes").insert(new_recipe).execute()
            if response.data:
                st.success(f"Successfully added {recipe_name}!")
                st.rerun()
            else:
                st.error("Failed to add recipe to the database. Please try again.")
else:
    recipe_selection = st.dataframe(
        recipes.iloc[:,1:2],
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row"
    )
    if len(recipe_selection['selection']['rows']) > 0:
        selected_id = recipes.iloc[recipe_selection['selection']['rows'][0]]['recipe_id']
        selected_recipe = recipes[recipes['recipe_id']==selected_id].iloc[0]
        rec_id = int(selected_recipe.to_list()[0])
        st.subheader("Current Ingredients", divider="blue")
        st.table(fetch_recipe_ingredients(rec_id))

        # --- Indented content starts here ---
        st.markdown("<br>", unsafe_allow_html=True)  # Line break before forms
        spacer, content = st.columns([0.5, 6])  # Reduced indent
        with content:
            st.subheader("Add New Ingredient",divider="blue")
            with st.form("new_ingredient_form", clear_on_submit=True):
                food_name = st.selectbox("Food Name", options=foods['food_name'])
                amount = st.number_input("Amount (g)", min_value=0.0, step=0.1)
                food_id = foods[foods['food_name']==food_name]['food_id'].to_list()[0]    
                ingredient_submitted = st.form_submit_button("Add Ingredient")
                if ingredient_submitted:
                    set_supabase_auth()
                    new_ingredient = {
                        "food_id": food_id,
                        "recipe_id": rec_id,
                        "amount": amount
                    }
                    response = supabase.table("recipe_ingredients").insert(new_ingredient).execute()
                    if response.data:
                        st.success(f"Successfully added {food_name} to the ingredients for {selected_recipe['recipe_name']}!")
                        st.rerun()
                    else:
                        st.error("Failed to add food to the database. Please try again.")

            st.write('***If the food you wish to add to the recipe does not exist yet, add it below***')

            st.subheader("Add New Food", divider='blue')
            with st.form("new_food_form", clear_on_submit=True):
                name = st.text_input("Food Name")
                protein = st.number_input("Protein Content (g)", min_value=0.0, step=0.1)
                carbs = st.number_input("Carbohydrate Content (g)", min_value=0.0, step=0.1)
                sugars = st.number_input("of which sugars (g)", min_value=0.0, step=0.1)
                fat = st.number_input("Fat Content (g)", min_value=0.0, step=0.1)
                sats = st.number_input("of which saturates (g)", min_value=0.0, step=0.1)
                fiber = st.number_input("Fiber Content (g)", min_value=0.0, step=0.1)
                food_submitted = st.form_submit_button("Add Food")
                if food_submitted:
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
                        st.error("Failed to add food to the database. Please try again.")
    else:
        st.info("Select a recipe to view or add ingredients.")
        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("Add New Recipe", divider='blue')
        with st.form("new_recipe_form", clear_on_submit=True):
            recipe_name = st.text_input("Recipe Name")
            submitted = st.form_submit_button("Add Recipe")
            if submitted:
                set_supabase_auth()
                current_time = datetime.now().isoformat()
                new_recipe = {
                    "recipe_name": recipe_name,
                    "created_at": current_time,
                    "updated_at": current_time
                }
                response = supabase.table("recipes").insert(new_recipe).execute()
                if response.data:
                    st.success(f"Successfully added {recipe_name}!")
                    st.rerun()
                else:
                    st.error("Failed to add recipe to the database. Please try again.")
