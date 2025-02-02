# Import required libraries
import streamlit as st
import datetime
from openai import OpenAI
import base64

# Read API Key from Streamlit Secrets
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
client = OpenAI(api_key=OPENAI_API_KEY)

# Streamlit UI for AI Trip Planner
st.title("🌍 AI Trip Planner")

# Step 1: User Inputs - Trip Budget
st.sidebar.header("💰 Trip Budget")
total_budget = st.sidebar.number_input("Total Budget ($)", min_value=100, value=2000)
accommodation_budget = st.sidebar.number_input("Accommodation Budget ($)", min_value=50, value=600)
food_budget = st.sidebar.number_input("Food Budget ($)", min_value=50, value=400)
entertainment_budget = st.sidebar.number_input("Entertainment Budget ($)", min_value=50, value=300)
shopping_budget = st.sidebar.number_input("Shopping Budget ($)", min_value=50, value=200)

# Step 2: Trip Details
st.header("Plan Your Trip")
destination = st.text_input("Enter your destination:")
start_date = st.date_input("Start Date", datetime.date.today())
end_date = st.date_input("End Date", datetime.date.today() + datetime.timedelta(days=3))
travel_companions = st.text_area("Who are you traveling with? (e.g., solo, family, friends, kids)")

# Meal Preferences
st.header("🍽️ Meal Preferences")
include_breakfast = st.checkbox("Include Breakfast in Itinerary")
include_lunch = st.checkbox("Include Lunch in Itinerary")
include_dinner = st.checkbox("Include Dinner in Itinerary")
meal_preferences = st.text_input("Any dietary restrictions or preferred cuisine?")

# Store itinerary
itinerary = ""

# Step 3: AI-Generated Stay Recommendations (Sidebar)
st.sidebar.header("🏨 Recommended Stays")
if destination:
    stay_prompt = f"""
    Suggest 3 accommodation options in {destination} that fit within a budget of ${accommodation_budget}.
    Provide the hotel name, a brief description, and estimated cost per night.
    """

    response_stay = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": "You are an AI travel assistant."},
                  {"role": "user", "content": stay_prompt}]
    )

    stay_recommendations = response_stay.choices[0].message.content
    st.sidebar.write(stay_recommendations)

# Step 4: Generate Itinerary with AI
if st.button("Generate Itinerary"):
    with st.spinner("Generating your personalized itinerary..."):
        itinerary_prompt = f"""
        Create a detailed, day-by-day travel itinerary for {destination} from {start_date} to {end_date}.
        Consider the following:
        - Who is traveling: {travel_companions}
        - Meals to include:
          - Breakfast: {'Yes' if include_breakfast else 'No'}
          - Lunch: {'Yes' if include_lunch else 'No'}
          - Dinner: {'Yes' if include_dinner else 'No'}
        - Meal Preferences: {meal_preferences}
        - Budget Considerations:
          - Food budget: ${food_budget} Include meal for 4 amount.
          - Entertainment budget: ${entertainment_budget} (Suggest activities within budget)
        - Suggest activities based on location, travel distance, and traveler type.
        - Ensure a well-paced, enjoyable trip.

        Provide the itinerary in a structured format and distance between one activity to the other or the dining places:
        - Day X: Morning activity, lunch, afternoon activity, dinner, evening activity.
        """

        # Call OpenAI GPT-4o for AI itinerary generation
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": "You are an AI travel assistant."},
                      {"role": "user", "content": itinerary_prompt}]
        )

        itinerary = response.choices[0].message.content

        # Store itinerary in session state
        st.session_state["itinerary"] = itinerary

# Display itinerary if available
if "itinerary" in st.session_state:
    st.subheader("📅 Your AI-Generated Itinerary")
    st.write(st.session_state["itinerary"])

    # Step 5: Allow User to Modify Itinerary
    st.subheader("🔄 Request Changes to Your Itinerary")
    user_modifications = st.text_area("Describe any changes you want (e.g., 'Replace museum visit with beach time')")

    if st.button("Update Itinerary"):
        with st.spinner("Updating itinerary based on your feedback..."):
            modify_prompt = f"""
            Modify the following travel itinerary based on the user's requested changes:
            ---
            {st.session_state["itinerary"]}
            ---
            User's requested changes: {user_modifications}
            ---
            Provide an updated itinerary considering these modifications.
            """

            response_modify = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": "You are an AI travel assistant."},
                          {"role": "user", "content": modify_prompt}]
            )

            updated_itinerary = response_modify.choices[0].message.content

            # Store updated itinerary
            st.session_state["itinerary"] = updated_itinerary

            # Display updated itinerary
            st.subheader("✅ Updated Itinerary")
            st.write(st.session_state["itinerary"])

    # Step 6: Share Itinerary (Generate Shareable Link & Download PDF)
    st.subheader("📤 Share Your Itinerary")

    # Generate a shareable link (Using base64 encoding)
    encoded_itinerary = base64.b64encode(st.session_state["itinerary"].encode()).decode()
    shareable_link = f"https://your-app.com/share?data={encoded_itinerary}"

    st.markdown(f"🔗 **Share this link with your friends:** [Copy Link]({shareable_link})")
    
    # Download as PDF
    if st.button("Download Itinerary as PDF"):
        pdf_file = "itinerary.pdf"
        pdfkit.from_string(st.session_state["itinerary"], pdf_file)

        with open(pdf_file, "rb") as file:
            pdf_base64 = base64.b64encode(file.read()).decode()
            pdf_href = f'<a href="data:application/pdf;base64,{pdf_base64}" download="itinerary.pdf">📥 Download PDF</a>'
            st.markdown(pdf_href, unsafe_allow_html=True)

# Step 7: Generate Customizable Packing List
st.subheader("🎒 AI-Powered Packing List")
packing_customization = st.text_area("Add any special requirements (e.g., 'Include hiking gear', 'Packing for cold weather')")

if st.button("Generate Smart Packing List"):
    with st.spinner("Creating your packing list..."):
        packing_prompt = f"""
        Based on the destination {destination}, weather conditions, and planned activities, 
        create a detailed packing list, including clothing, accessories, gadgets, and any necessary items.

        Additional user input: {packing_customization}
        """

        response_packing = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": "You are an AI packing assistant."},
                      {"role": "user", "content": packing_prompt}]
        )

        packing_list = response_packing.choices[0].message.content

        # Display packing list
        st.subheader("✅ Your AI-Powered Packing List")
        st.write(packing_list)

# Step 8: Future Enhancements
st.markdown("### 🚀 Upcoming Features")
st.markdown("- 🌦️ Weather-based itinerary adjustments")
st.markdown("- 📍 Google Maps integration for real-time restaurant and attraction recommendations")
st.markdown("- 🔄 Offline itinerary access for travel convenience")
