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

def fetch_data(table):
    set_supabase_auth()
    response = supabase.table(table).select("*").execute()
    return pd.DataFrame(response.data)


def fetch_meal_foods(meal_id):
    set_supabase_auth()
    response = supabase.table("meal_foods").select("*").eq("meal_id", meal_id).execute()
    return pd.DataFrame(response.data)

def fetch_meal_recipes(meal_id):
    set_supabase_auth()
    response = supabase.table("meal_recipes").select("*").eq("meal_id", meal_id).execute()
    return pd.DataFrame(response.data)     

meals = fetch_data("meals")
recipes = fetch_data("recipes")
foods = fetch_data("foods")

# Session state initialization
if "meal_content" not in st.session_state:
    st.session_state.meal_content = {"foods": [], "recipes": []}
if "add_foods" not in st.session_state:
    st.session_state.add_foods = False
if "meal_name" not in st.session_state:
    st.session_state.meal_name = ""
if "source_selector" not in st.session_state:
    st.session_state.source_selector = "Foods"

st.title("Meals")


if not st.session_state.add_foods:
    st.subheader("Add a new meal", divider="blue")
    with st.form("new_meal_form", clear_on_submit=True):
        meal_types = ['Breakfast', 'Lunch', 'Dinner', 'Shake', 'Snack']
        meal_name = st.selectbox("Which Meal?", meal_types)
        
        if st.form_submit_button("Start Adding Foods"):
            set_supabase_auth()
            current_time = datetime.now().isoformat()
            
            # Create initial meal record
            new_meal = {
                "user_id": st.session_state.session.user.id,
                "meal_desc": meal_name,
                "created_at": current_time
            }
            
            # Insert meal and get generated ID
            response = supabase.table("meals").insert(new_meal).execute()
            
            if response.data:
                st.session_state.meal_id = response.data[0]['meal_id']
                st.session_state.add_foods = True
                st.session_state.meal_name = meal_name
                st.rerun()
            else:
                st.error("Failed to create meal entry")

else:
    now = datetime.now()
    st.subheader(f'New {st.session_state.meal_name} ({now.strftime("%d %b %y @")} {now.strftime("%I.%M%p").lstrip("0")})'
                 ,divider='blue')
    st.markdown(
        '<span style="font-size: 1.1em; font-weight: 600; color: #333;">Current contents:</span>',
        unsafe_allow_html=True
    )
    iter = 1
    for food in st.session_state.meal_content['foods']:
        st.write(f'{iter}. {food[1]}g of {food[0]}')
        iter += 1
    for recipe in st.session_state.meal_content['recipes']:
        st.write(f'{iter}. {recipe[1]}g of {recipe[0]}')
        iter += 1
    
    st.write("")
    if iter > 1:
        with st.form("finalize_meal", border=False):
            if st.form_submit_button("Save Meal"):
                set_supabase_auth()
                current_time = datetime.now().isoformat()

                for food in st.session_state.meal_content["foods"]:
                    st.write(f'Add {food[1]}g of {food[0]} to meal_foods')
                    food_id = int(foods[foods['food_name'] == food[0]]['food_id'].iloc[0])
                    new_meal_food = {
                        "meal_id": st.session_state.meal_id,
                        "food_id": food_id,
                        "amount": food[1],
                        "user_id": st.session_state.session.user.id
                    }
                    st.write(new_meal_food)
                    response = supabase.table("meal_foods").insert(new_meal_food).execute()

                for recipe in st.session_state.meal_content["recipes"]:
                    st.write(f'Add {recipe[1]}g of {recipe[0]} to meal_recipes')
                    recipe_id = int(recipes[recipes['recipe_name'] == recipe[0]]['recipe_id'].iloc[0])
                    new_meal_recipe = {
                        "meal_id": st.session_state.meal_id,
                        "recipe_id": recipe_id,
                        "amount": recipe[1],
                        "user_id": st.session_state.session.user.id
                    }
                    st.write(new_meal_recipe)
                    response = supabase.table("meal_recipes").insert(new_meal_recipe).execute()

            
                # Session state reset
                st.session_state.meal_content = {"foods": [], "recipes": []}
                st.session_state.add_foods = False
                st.session_state.meal_name = ""
                st.rerun()
    
    st.write("")
    
    # Create two columns, the first is a spacer
    spacer, content, spacer = st.columns([2, 50, 2])  # Adjust ratio as needed for indentation

    with content:
        
        with st.container(border=True):
            st.markdown(
                '<span style="font-size: 1.1em; font-weight: 600; color: #333;">Add Foods/Recipes</span>',
                unsafe_allow_html=True
            )
    
            source = st.radio("Source", ['Foods', 'Recipes'], key='source_selector')

            with st.form("add_food", clear_on_submit=True, border=False):
                if st.session_state.source_selector == 'Foods':
                    new_food = st.selectbox('Which Food?', foods['food_name'])
                else:
                    new_food = st.selectbox('Which Recipe?', recipes['recipe_name'])

                new_amount = st.number_input("Amount (g)", min_value=0.0, step=0.1)

                if st.form_submit_button("Add to Meal"):
                    if st.session_state.source_selector == 'Foods':
                        st.session_state.meal_content["foods"] += [[new_food, new_amount]]
                    else:
                        st.session_state.meal_content["recipes"] += [[new_food, new_amount]]
                    st.success(f"Added {new_amount}g of {new_food}!")
                    st.rerun()


if not st.session_state.add_foods:
    with st.expander("View Previous Meals"):
        meals = fetch_data("meals")
        meals["created_at"] = pd.to_datetime(meals["created_at"])
        if "selected_meal" not in st.session_state:
            st.session_state.selected_meal = None

        # Display meals dataframe
        meal_display = st.dataframe(
            meals.iloc[:, :-1],
            hide_index=True,
            key="meal_table",
            selection_mode="single-row",  # <-- Enable row selection
            on_select="rerun",
            column_config={
                "meal_desc": "Meal Type",
                "created_at": st.column_config.DatetimeColumn("Logged At")
            }
        )

        if len(meal_display["selection"]['rows']) > 0:
            rowid = meal_display["selection"]['rows']
            st.session_state.selected_meal = meals.iloc[rowid]["meal_id"].iloc[0]
            meal_foods = fetch_meal_foods(st.session_state.selected_meal)
            meal_recipes = fetch_meal_recipes(st.session_state.selected_meal)
            for idx, row in meal_foods.iterrows():
                amt = row['amount']
                fd = foods[foods['food_id']==row['food_id']]['food_name'].iloc[0]
                st.write(f'{amt}g of {fd}')

            for idx, row in meal_recipes.iterrows():
                amt = row['amount']
                fd = recipes[recipes['recipe_id']==row['recipe_id']]['recipe_name'].iloc[0]
                st.write(f'{amt}g of {fd}')


        
    