from PIL import Image
import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime
from wordcloud import WordCloud
import io

# Function to inject tooltip CSS and render a tooltip
def add_tooltip_css():
    """
    Adds the tooltip CSS to the Streamlit app.
    """
    st.markdown(f"""
        <style>
        .tooltip {{
            position: relative;
            display: inline-block;
            cursor: pointer;
            color: #007BFF; /* Blue color for the info icon */
            font-weight: normal;
            margin-left: 10px; /* Add spacing between text and icon */
            font-size: 18px; /* Adjust the size of the icon */
        }}
        .tooltip .tooltiptext {{
            visibility: hidden;
            width: 250px; /* Adjust the width of the tooltip box */
            background-color: #333; /* Dark background for contrast */
            color: #fff; /* White text for readability */
            text-align: left; /* Align text to the left */
            border-radius: 6px;
            padding: 8px; /* Add padding for better readability */
            position: absolute;
            z-index: 1;
            top: 50%; /* Align vertically with the icon */
            left: 110%; /* Position it to the right of the icon */
            transform: translateY(-50%); /* Center vertically */
            opacity: 0; /* Hidden by default */
            transition: opacity 0.3s; /* Smooth transition */
        }}
        .tooltip:hover .tooltiptext {{
            visibility: visible;
            opacity: 1;
        }}
        </style>
    """, unsafe_allow_html=True)

def render_tooltip(info_text: str, icon: str = "ℹ️") -> str:
    """
    Returns the HTML code for a tooltip.
    Parameters:
    - info_text (str): The text to display inside the tooltip.
    - icon (str): The icon or text to display for the tooltip (default: ℹ️).
    """
    return f"""
    <div class="tooltip">{icon}
      <span class="tooltiptext">{info_text}</span>
    </div>
    """
# add_tooltip_css()
# tooltip_html = render_tooltip("This is a helpful tooltip for the title.")

st.set_page_config(
    page_title="Dashboard",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)
st.markdown(
    """
    <style>
    .css-1d3912d {  /* This selector targets the Streamlit's dark theme toggle button */
        background-color: #000;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True
)

def add_custom_css():
    st.markdown(
        """
        <style>
        .card {
            background-color: #1e1e1e;
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            font-size: 20px;
            box-shadow: 2px 2px 10px rgba(0,0,0,0.5);
        }
        .card-container {
            position: absolute;
            top: 20px;  /* Adjust to place the card lower or higher */
            right: 20px;  /* Adjust to place the card further left or right */
            display: flex;
            gap: 10px;
            margin-bottom: 100px;  /* Increased space below the cards */
        }
        </style>
        """,
        unsafe_allow_html=True
    )

def load_data(file_path):
    df = pd.read_csv(file_path, parse_dates=False)  # Don't parse dates initially
    date_columns = ['Order_Created_At', 'Order_Updated_At','Event_Time','Customer_Created_At','Customer_Updated_At','Order_Created_At','Order_Updated_At','Variant_Created_At','Product_Created_At']
    for col in df.columns:
        if col in date_columns and df[col].dtype == 'object':  # Only convert the specified columns
            try:
                df[col] = pd.to_datetime(df[col], errors='coerce', utc=True)
            except Exception as e:
                st.error(f"Error parsing column '{col}': {e}")
    return df

# Load the datasets
df_abandoned_checkouts = load_data('D:\\All_New_Data\\dyori_AbandonedCheckouts.csv')
df_cj = load_data('D:\\All_New_Data\\dyori_CJ.csv')
df_customers = load_data('D:\\All_New_Data\\dyori_Customers_Dataset.csv')
df_orders = load_data('D:\\All_New_Data\\dyori_Orders_Dataset.csv')
df_products = load_data('D:\\All_New_Data\\dyori_Products_Dataset.csv')

def filter_by_date(df, date_column, label_prefix=""):
    min_date = df[date_column].min().date()
    max_date = df[date_column].max().date()
    start_date = st.sidebar.date_input(f'{label_prefix}Start Date', min_value=min_date, max_value=max_date,value=min_date)
    end_date = st.sidebar.date_input(f'{label_prefix}End Date', min_value=min_date, max_value=max_date, value=max_date)
    if start_date and end_date:
        start_date = pd.to_datetime(start_date).tz_localize('UTC')
        end_date = pd.to_datetime(end_date).tz_localize('UTC')
        df[date_column] = pd.to_datetime(df[date_column])
        filtered_data = df[(df[date_column] >= start_date) & (df[date_column] <= end_date)]
        return filtered_data
    return df

def show_customer_data_page():
    st.title('Customer Data')
    add_custom_css()
    # Todo- Card Creation for the above
    col1, col2, col3 = st.columns(3)  # Fixed from 2 to 3
    with col1:
        total_listed_customers = df_customers['Customer_ID'].nunique()
        st.markdown(
            f"""
            <div class="card">
                <p>Total Listed Customers</p>
                <h1>{total_listed_customers}</h1>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col2:
        total_paying_customers = df_orders['Customer_ID'].nunique()
        st.markdown(
            f"""
            <div class="card">
                <p>Total Paying Customers</p>
                <h1>{total_paying_customers}</h1>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col3:
        if 'Customer_Name' in df_orders.columns and 'Order_Total_Price' in df_orders.columns:
            customer_summary = df_orders.groupby("Order_ID").agg(
                Total_Spending=("Order_Total_Price", 'first'),  # Total spending for each Order_ID
                Customer_Name=("Customer_Name", 'first')  # Get the first customer for each Order_ID
            ).reset_index()

            customer_summary1 = customer_summary.groupby("Customer_Name").agg(
                Orders_Placed=("Order_ID", "nunique"),  # Count of unique orders per Customer_Name
                Total_Spending=("Total_Spending", 'sum'),  # Total spending for each Customer_Name
            ).reset_index()

            customer_summary1 = customer_summary1[customer_summary1['Orders_Placed'] >= 2]
            repeat_customers = customer_summary1.shape[0]  # Get the count of repeat customers
            st.markdown(
                f"""
                <div class="card">
                    <p>Repeat Customers</p>
                    <h1>{repeat_customers}</h1>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            st.markdown("Data columns 'Customer_Name' or 'Order_Total_Price' are missing from the dataframe.")

    st.title("Preview Filtered Customer Data")
    st.subheader("Customer Data")
    filtered_customers = filter_by_date(df_customers, 'Customer_Created_At')
    # with st.expander("Preview Filtered Customer Data"):
    st.dataframe(filtered_customers,use_container_width=True)
    #Todo- Customer Name Top 5 and Least 5 with Price Spends----------------------------------------
    order_df = df_orders.drop_duplicates("Order_ID")
    order_data = order_df.groupby('Customer_Name')['Order_Total_Price'].sum().reset_index()
    order_data = order_data.dropna(subset=['Customer_Name'])
    top_5_customers = order_data.nlargest(50, 'Order_Total_Price')
    least_5_customers = order_data.nsmallest(50, 'Order_Total_Price')
    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        top_n = st.slider("Select Top N IPs to Display", min_value=1, max_value=50, value=5)
        # Filter top N customers by total order price
        top_5_customers_filtered = top_5_customers.nlargest(top_n, 'Order_Total_Price')
        st.markdown("<h3 style='text-align: center;'>Top N Customers by Total Order Price</h3>", unsafe_allow_html=True)
        # Create the bar chart
        chart = alt.Chart(top_5_customers_filtered).mark_bar().encode(
            x=alt.X('Customer_Name:O', title='Customer Name',
                    sort=top_5_customers_filtered['Order_Total_Price'].tolist()),
            y=alt.Y('Order_Total_Price:Q', title='Total Order Price (€)'),
            color=alt.Color('Order_Total_Price:Q', legend=None),
            tooltip=['Customer_Name:N', 'Order_Total_Price:Q']
        ).properties(
            width=700,
            height=400,
            title="Top N Customers by Total Order Price"
        )
        # Add text labels on the bars
        text = chart.mark_text(
            align='center',
            baseline='middle',
            dy=-10,  # Adjust the vertical position of the text
            fontSize=12
        ).encode(
            text='Order_Total_Price:Q'
        )
        # Combine the chart and the text
        final_chart = chart + text
        # Configure axis for better readability
        final_chart = final_chart.configure_axis(
            labelAngle=0,  # Horizontal x-axis labels
            labelFontSize=12,
            titleFontSize=14
        )
        # Display the final chart
        st.altair_chart(final_chart, use_container_width=True)

    with chart_col2:
        top_n = st.slider("Select Least N IPs to Display", min_value=1, max_value=50, value=5)
        # Filter least N customers by total order price
        least_5_customers_filtered = least_5_customers.nsmallest(top_n, 'Order_Total_Price')
        st.markdown("<h3 style='text-align: center;'>Least N Customers by Total Order Price</h3>",unsafe_allow_html=True)
        # Create the bar chart
        chart = alt.Chart(least_5_customers_filtered).mark_bar().encode(
            x=alt.X('Customer_Name:O', title='Customer Name',
                    sort=least_5_customers_filtered['Order_Total_Price'].tolist()),
            y=alt.Y('Order_Total_Price:Q', title='Total Order Price (€)'),
            color=alt.Color('Order_Total_Price:Q', legend=None),
            tooltip=['Customer_Name:N', 'Order_Total_Price:Q']
        ).properties(
            width=700,
            height=400,
            title="Least N Customers by Total Order Price"
        )
        # Add text labels on the bars
        text = chart.mark_text(
            align='center',
            baseline='middle',
            dy=-10,  # Adjust the vertical position of the text
            fontSize=12
        ).encode(
            text='Order_Total_Price:Q'
        )
        # Combine the chart and the text
        final_chart = chart + text
        # Configure axis for better readability
        final_chart = final_chart.configure_axis(
            labelAngle=0,  # Horizontal x-axis labels
            labelFontSize=12,
            titleFontSize=14
        )
        # Display the final chart
        st.altair_chart(final_chart, use_container_width=True)
    #Todo- Customer Summery Table with Total Spend- Uniques Customer Names
    customer_summary = df_orders.groupby("Order_ID").agg(
        Total_Spending=("Order_Total_Price", 'first'),
        Customer_Name=("Customer_Name", "first")
    ).reset_index()
    customer_summary1 = customer_summary.groupby("Customer_Name").agg(
        Orders_Placed=("Order_ID", "nunique"),
        Total_Spending=("Total_Spending", 'sum'),
    ).reset_index()
    customer_summary1 = customer_summary1[customer_summary1['Orders_Placed'] >= 2]
    customer_summary1 = customer_summary1.reset_index(drop=True)
    st.title("Customer Order Summary")
    st.subheader("Summary Table")
    with st.expander("Preview Filtered Customer Data"):
        st.dataframe(customer_summary1, use_container_width=True)

    #Todo Bar Graph for Customer province_data and Country data with unique count
    province_data = df_customers.groupby("Customer_Province")["Customer_ID"].nunique().reset_index()
    province_data = province_data.rename(columns={"Customer_ID": "Unique_Customers"})
    country_data = df_customers.groupby("Customer_Country")["Customer_ID"].nunique().reset_index()
    country_data = country_data.rename(columns={"Customer_ID": "Unique_Customers"})
    # Create columns for charts
    chart_col1, chart_col2 = st.columns(2)
    # Bar Chart for Customer_Province
    with chart_col1:
        st.markdown("<h3 style='text-align: center;'>Unique Customers by Province</h3>", unsafe_allow_html=True)
        province_chart = alt.Chart(province_data).mark_bar().encode(
            x=alt.X("Customer_Province:O", title="Customer Province", sort="-y"),
            y=alt.Y("Unique_Customers:Q", title="Number of Unique Customers"),
            color=alt.Color("Customer_Province:N", legend=None),
            tooltip=["Customer_Province", "Unique_Customers"]
        ).properties(width=350, height=300)

        province_chart_text = province_chart.mark_text(
            align='center',
            baseline='middle',
            dy=-10,
            fontSize=12
        ).encode(
            text='Unique_Customers:Q'
        )
        province_chart = province_chart + province_chart_text
        province_chart = province_chart.configure_axis(
            labelAngle=0,
            labelFontSize=14,
            titleFontSize=16
        )
        st.altair_chart(province_chart, use_container_width=True)
    # Bar Chart for Customer_Country
    with chart_col2:
        st.markdown("<h3 style='text-align: center;'>Unique Customers by Country</h3>", unsafe_allow_html=True)
        # Create the Altair chart for unique customers by country
        country_chart = alt.Chart(country_data).mark_bar().encode(
            x=alt.X("Customer_Country:O", title="Customer Country", sort="-y"),
            y=alt.Y("Unique_Customers:Q", title="Number of Unique Customers"),
            color=alt.Color("Unique_Customers:Q", legend=None),  # Color the bars based on unique customers count
            tooltip=["Customer_Country", "Unique_Customers"]
        ).properties(width=350, height=300)
        # Add text labels to display the number of unique customers on top of the bars
        country_chart_text = country_chart.mark_text(
            align='center',
            baseline='middle',
            dy=-10,  # Adjust the vertical position of the text
            fontSize=12
        ).encode(
            text='Unique_Customers:Q'
        )
        # Combine the bar chart with the text labels
        country_chart = country_chart + country_chart_text
        # Configure the axis for better readability
        country_chart = country_chart.configure_axis(
            labelAngle=0,  # Set the angle of the axis labels (x-axis) to 0 degrees
            labelFontSize=14,  # Increase font size of labels
            titleFontSize=16  # Increase font size of axis title
        )
        # Display the final chart
        st.altair_chart(country_chart, use_container_width=True)

def show_cj_page():
    st.title('Customer Journey Data')
    add_custom_css()
    # Todo- Card Creation for the above
    col1, col2,col3 = st.columns(3)  # Fixed from 2 to 3
    with col1:
        total_listed_customers = df_cj['Customer_IP'].nunique()
        st.markdown(
            f"""
                <div class="card">
                    <p>Total Viewers</p>
                    <h1>{total_listed_customers}</h1>
                </div>
                """,
            unsafe_allow_html=True
        )

    with col2:
        max_session_df = df_cj.loc[df_cj.groupby('Customer_IP')['session'].idxmax()]
        customer_summary1 = max_session_df[max_session_df['session'] >= 2]
        repeat_customers = customer_summary1.shape[0]
        st.markdown(
            f"""
                        <div class="card">
                            <p>Repeat Viewers</p>
                            <h1>{repeat_customers}</h1>
                        </div>
                        """,
            unsafe_allow_html=True
        )

    with col3:
        max_session_df = df_cj.loc[df_cj.groupby('Customer_IP')['session'].idxmax()]
        session_sum = max_session_df['session'].sum()
        st.markdown(
            f"""
                        <div class="card">
                            <p>Total sessions</p>
                            <h1>{session_sum}</h1>
                        </div>
                        """,
            unsafe_allow_html=True
        )
    st.title("Preview Filtered Customer Journey Data")
    st.subheader("Customer Journey Data")
    filtered_cj = filter_by_date(df_cj, 'Event_Time')
    # with st.expander("Preview Filtered CJ Data"):
    st.dataframe(filtered_cj,use_container_width=True)

    # #Todo- Session details on weekdays and Weekends
    col1 = st.columns(1)[0]  # Create a single column
    with col1:
        add_tooltip_css()
        tooltip_html = render_tooltip("This chart compares the total number of sessions on weekdays and weekends based on event timestamps. The data is grouped by unique customer sessions. Hover over the chart to see detailed information, including the category (Weekday or Weekend), the session count, and the percentage representation.")
        # st.title(f'Total sessions: weekday vs weekend {tooltip_html}')
        st.markdown(
            f"<h1 style='display: inline-block;'>Total sessions: weekday vs weekend {tooltip_html}</h1>", unsafe_allow_html=True
        )
        df_cj['Event_Time'] = pd.to_datetime(df_cj['Event_Time'], errors='coerce',utc=True)  # Ensure Event_Time is in datetime format
        df_cj['Weekday_Weekend'] = df_cj['Event_Time'].dt.dayofweek.apply(
            lambda x: 'Weekend' if x >= 5 else 'Weekday'
        )
        filtered_df = df_cj
        grouped_filtered_df = filtered_df.groupby(['Customer_IP', 'session']).first().reset_index()
        weekday_count = grouped_filtered_df[grouped_filtered_df['Weekday_Weekend'] == 'Weekday'].shape[0]
        weekend_count = grouped_filtered_df[grouped_filtered_df['Weekday_Weekend'] == 'Weekend'].shape[0]
        counts = [weekday_count, weekend_count]
        labels = ['Weekday', 'Weekend']
        st.write(f"Weekday Count: {weekday_count} ({(weekday_count / sum(counts)) * 100:.2f}%)")
        st.write(f"Weekend Count: {weekend_count} ({(weekend_count / sum(counts)) * 100:.2f}%)")
        pie_data = pd.DataFrame({
            'Category': labels,
            'Count': counts,
            'Percentage': [(count / sum(counts)) * 100 for count in counts]  # Calculate percentage
        })
        pie_data['Label'] = pie_data['Percentage'].round(1).astype(str) + '%'  # Only show the percentage
        # Create the pie chart with Altair
        pie_chart = alt.Chart(pie_data).mark_arc().encode(
            theta=alt.Theta(field="Count", type="quantitative"),
            color=alt.Color(field="Category", type="nominal"),
            tooltip=["Category", "Count", "Percentage"],  # Show both count and percentage in tooltip
        )

        final_chart = pie_chart
        st.altair_chart(final_chart, use_container_width=True)

    #Todo-Total session duration-Average session duration-Least session duration-Highest session duration
    def convert_seconds(seconds):
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours} hr {minutes} mini"
    col1, col2,col3 = st.columns(3)
    df_cj['Event_Time'] = pd.to_datetime(df_cj['Event_Time'])
    groupby_session = df_cj.groupby(['session', 'Customer_IP']).agg(
        Time_On_Page=('Time_On_Page', 'sum')
    ).reset_index()
    overall_sum = groupby_session['Time_On_Page'].sum()
    Average_data = groupby_session['Time_On_Page'].mean()
    overall_sum = convert_seconds(overall_sum)
    overall_average = convert_seconds(Average_data)
    #Todo-Average_number of session per customer---------------------------
    session_count_per_customer = df_cj.groupby('Customer_IP')['session'].max().reset_index()
    average_sessions_per_customer = session_count_per_customer['session'].mean()
    average_sessions_per_customer = round(average_sessions_per_customer, 2)
    with col1:
        st.markdown(
            f"""
                <div class="card">
                    <p>Total session duration</p>
                    <h1>{overall_sum}</h1>
                </div>
                """,
            unsafe_allow_html=True
        )
    with col2:
        st.markdown(
            f"""
                <div class="card">
                    <p>Average session duration</p>
                    <h1>{overall_average}</h1>
                </div>
                        """,
            unsafe_allow_html=True
        )
    with col3:
        st.markdown(
            f"""
                       <div class="card">
                           <p>Average number of sessions per customer</p>
                           <h1>{average_sessions_per_customer}</h1>
                       </div>
                       """,
            unsafe_allow_html=True
        )
    #Todo- List of TOP 10 customer on pages with time spent in each Events
    groupby_session = df_cj.groupby(['session', 'Customer_IP']).agg(
        Time_On_Page=('Time_On_Page', 'sum'),
        Event_time=('Event_Time', 'first')
    ).reset_index()
    groupby_session['Event_time'] = groupby_session['Event_time'].dt.date
    top_5_rows = groupby_session.nlargest(10, 'Time_On_Page')
    top_5_rows['Time_On_Page'] = top_5_rows['Time_On_Page'].apply(convert_seconds)
    top_5_rows = top_5_rows.drop(columns=['session'])
    st.title("Top 10 Customer IP List Data")
    st.subheader("Summary Table")
    # with st.expander("List of Customer on Page"):
    st.dataframe(top_5_rows, use_container_width=True)
    #Todo-Viewers with highest number of sessions
    max_session_per_ip = df_cj.groupby('Customer_IP')['session'].max().reset_index()
    # st.title("Maximum Sessions per Customer IP")
    add_tooltip_css()
    tooltip_html = render_tooltip(
        "This chart displays the maximum number of sessions per customer IP. The x-axis represents unique Customer IPs, and the y-axis shows the maximum session count for each IP. Hover over the bars to see the Customer IP and its corresponding session count. Use the slider to adjust the number of top IPs displayed."
        )
    st.markdown(
        f"<h1 style='display: inline-block;'>Maximum Sessions per Customer IP {tooltip_html}</h1>",
        unsafe_allow_html=True
    )
    top_n = st.slider("Select Top N IPs to Display", min_value=1, max_value=50, value=10)
    top_n_ip = max_session_per_ip.nlargest(top_n, 'session')
    st.markdown("<h3 style='text-align: center;'>Maximum Sessions per Customer IP</h3>", unsafe_allow_html=True)
    # Create the bar chart
    chart = alt.Chart(top_n_ip).mark_bar().encode(
        x=alt.X("Customer_IP:N", title="Customer IP", sort="-y"),  # Set Customer_IP to x-axis
        y=alt.Y("session:Q", title="Max Session"),  # Set session to y-axis
        color=alt.Color("session:Q", legend=None),  # Color bars based on session count
        tooltip=["Customer_IP", "session"]
    ).properties(
        width=700,
        height=400,
        title="Maximum Sessions per Customer IP"
    )
    # Add text labels on the bars
    text = chart.mark_text(
        align='center',
        baseline='middle',
        dy=-10,  # Adjust the vertical position of the text
        fontSize=12
    ).encode(
        text='session:Q'
    )
    # Combine the chart and the text
    final_chart = chart + text

    # Configure axis for better readability
    final_chart = final_chart.configure_axis(
        labelAngle=0,  # Horizontal x-axis labels
        labelFontSize=12,
        titleFontSize=14
    )
    # Display the final chart
    st.altair_chart(final_chart, use_container_width=True)

    #Todo-Total sessions: day, month, quarter, year
    df_cj['day'] = df_cj['Event_Time'].dt.date
    # Ensure session column is numeric
    df_cj['session'] = pd.to_numeric(df_cj['session'], errors='coerce')
    # Compute session counts
    session_count_per_customer = df_cj.groupby(['Customer_IP', 'day'])['session'].nunique().reset_index()
    session_count_per_day = session_count_per_customer.groupby('day')['session'].sum().reset_index()
    # Create a complete date range
    start_date = session_count_per_day['day'].min()
    end_date = datetime.today().date()  # Use the current system date as the end date
    full_date_range = pd.date_range(start=start_date, end=end_date)
    # Reindex session_count_per_day to include all dates
    session_count_per_day.set_index('day', inplace=True)
    session_count_per_day = session_count_per_day.reindex(full_date_range, fill_value=0).reset_index()
    # Rename the columns
    session_count_per_day.rename(columns={'index': 'day', 'session': 'session_count'}, inplace=True)
    # Update the month column to use full month names
    session_count_per_day['month'] = session_count_per_day['day'].dt.strftime('%B %Y')  # Month-Year (e.g., January 2024)
    session_count_per_day['month'] = session_count_per_day['day'].dt.strftime('%Y-%m')  # Use Year-Month format (e.g., 2024-01)
    session_count_per_month = session_count_per_day.groupby('month')['session_count'].sum().reset_index()

    # Ensure months are sorted chronologically (including January data)
    session_count_per_month['month'] = pd.to_datetime(session_count_per_month['month'], format='%Y-%m')
    session_count_per_month = session_count_per_month.sort_values(by='month', ascending=True)
    # Group by Quarter
    session_count_per_day['quarter'] = session_count_per_day['day'].dt.to_period('Q').astype(str)
    session_count_per_quarter = session_count_per_day.groupby('quarter')['session_count'].sum().reset_index()
    # Group by Year
    session_count_per_day['Year'] = session_count_per_day['day'].dt.year
    session_count_per_Year = session_count_per_day.groupby('Year')['session_count'].sum().reset_index()

    # st.title('Session Count Visualizations')
    add_tooltip_css()
    tooltip_html = render_tooltip(
        "This visualization displays session counts across different time periods (day, month, quarter, year). The x-axis represents the time period, and the y-axis shows the total session count. Use the radio buttons above to switch between views. Hover over the points for detailed session information."
        )
    st.markdown(
        f"<h1 style='display: inline-block;'>Session Count Visualizations {tooltip_html}</h1>", unsafe_allow_html=True
    )
    view = st.radio("Select View",['Sessions per Day', 'Sessions per Month', 'Sessions per Quarter', 'Sessions per Year'])
    # For the "Sessions per Day" view
    if view == 'Sessions per Day':
        st.write("### Sessions per Day")
        # Define the line chart
        chart_day = alt.Chart(session_count_per_day).mark_line().encode(
            x=alt.X(
                'day:T',
                title='Date',
                axis=alt.Axis(format="%b %d, %Y", labelAngle=90, tickMinStep=1)  # Adjust x-axis labels
            ),
            y=alt.Y('session_count:Q', title='Number of Sessions')
        ).properties(title='Sessions per Day')
        # Define the points for emphasis
        points_day = alt.Chart(session_count_per_day).mark_point(size=60, color='red').encode(
            x='day:T',
            y='session_count:Q',
            tooltip=['day:T', 'session_count:Q']
        )
        # Combine line chart and points
        combined_chart_day = chart_day + points_day
        # Display the combined chart
        st.altair_chart(combined_chart_day, use_container_width=True)


    # For the "Sessions per Month" view
    elif view == 'Sessions per Month':
        st.write("### Sessions per Month")
        chart_month = alt.Chart(session_count_per_month).mark_line().encode(
            x=alt.X('month:T', title=None, axis=alt.Axis(tickCount=5, format='%b %Y', labelAngle=-90)),
            y='session_count:Q'
        ).properties(title='Sessions per Month')

        points_month = alt.Chart(session_count_per_month).mark_point(size=60, color='red').encode(
            x='month:T',
            y='session_count:Q',
            tooltip=['month:T', 'session_count:Q']
        )
        combined_chart_month = chart_month + points_month
        st.altair_chart(combined_chart_month, use_container_width=True)

    # For the "Sessions per Quarter" view
    elif view == 'Sessions per Quarter':
        st.write("### Sessions per Quarter")
        chart_quarter = alt.Chart(session_count_per_quarter).mark_line().encode(
            x='quarter:N',
            y='session_count:Q'
        ).properties(title='Sessions per Quarter')

        points_quarter = alt.Chart(session_count_per_quarter).mark_point(size=60, color='red').encode(
            x='quarter:N',
            y='session_count:Q',
            tooltip=['quarter:N', 'session_count:Q']
        )
        combined_chart_quarter = chart_quarter + points_quarter
        st.altair_chart(combined_chart_quarter, use_container_width=True)

    # For the "Sessions per Year" view
    elif view == 'Sessions per Year':
        st.write("### Sessions per Year")
        chart_year = alt.Chart(session_count_per_Year).mark_line().encode(
            x='Year:N',
            y='session_count:Q'
        ).properties(title='Sessions per Year')

        points_year = alt.Chart(session_count_per_Year).mark_point(size=60, color='red').encode(
            x='Year:N',
            y='session_count:Q',
            tooltip=['Year:N', 'session_count:Q']
        )
        combined_chart_year = chart_year + points_year
        st.altair_chart(combined_chart_year, use_container_width=True)

    # Update the month column to use full month names (with year)

    elif view == 'Sessions per Month':
        st.write("### Sessions per Month")
        # Make sure January data is included and months are properly sorted
        chart = alt.Chart(session_count_per_month).mark_line().encode(  # Changed to line chart
            x=alt.X('month:T', title=None, axis=alt.Axis(tickCount=5, format='%b %Y', labelAngle=-90)),
            # Labels rotated to vertical
            y='session_count:Q'
        ).properties(title='Sessions per Month')
        st.altair_chart(chart, use_container_width=True)

    elif view == 'Sessions per Quarter':
        st.write("### Sessions per Quarter")
        chart_quarter = alt.Chart(session_count_per_quarter).mark_line().encode(
            x='quarter:N',
            y='session_count:Q'
        ).properties(title='Sessions per Quarter')
        st.altair_chart(chart_quarter, use_container_width=True)

    elif view == 'Sessions per Year':
        st.write("### Sessions per Year")
        chart_year = alt.Chart(session_count_per_Year).mark_line().encode(
            x='Year:N',
            y='session_count:Q'
        ).properties(title='Sessions per Year')
        st.altair_chart(chart_year, use_container_width=True)

    # Todo-Most viewed product and collections logic (same as your current code)
    df_product_grouped = df_cj.groupby('Product_Name')['Customer_IP'].nunique().reset_index()
    df_product_grouped.rename(columns={'Customer_IP': 'Unique_Visitors'}, inplace=True)
    df_product_sorted = df_product_grouped.sort_values('Unique_Visitors', ascending=False)
    df_collection_grouped = df_cj.groupby('Collection_Name')['Customer_IP'].nunique().reset_index()
    df_collection_grouped.rename(columns={'Customer_IP': 'Unique_Visitors'}, inplace=True)
    df_collection_sorted = df_collection_grouped.sort_values('Unique_Visitors', ascending=False)
    # Create two columns for charts
    chart_col1, chart_col2 = st.columns(2)
    # Top N most popular products chart
    with chart_col1:
        # st.title('Most Popular Products by Unique Visitors')
        add_tooltip_css()
        tooltip_html = render_tooltip("This chart displays the top N most popular products based on the number of unique visitors. The x-axis represents the product names, and the y-axis shows the number of unique visitors. Use the slider above to select how many top products to display. Hover over the bars for detailed information about each product's unique visitors count.")
        st.markdown( f"<h1 style='display: inline-block;'>Most Popular Products  by Unique Visitors {tooltip_html}</h1>",unsafe_allow_html=True)
        top_n_products = st.slider("Select Top N Products to Display", min_value=1, max_value=50, value=10)
        df_top_n_product = df_product_sorted.head(top_n_products)
        st.markdown("<h3 style='text-align: center;'>Top N Most Popular Products</h3>", unsafe_allow_html=True)

        product_chart = alt.Chart(df_top_n_product).mark_bar().encode(
            x=alt.X('Product_Name:N', title='Product Name', sort=df_top_n_product['Unique_Visitors'].tolist(),
                    axis=alt.Axis(labelAngle=90)),  # Adjust labels angle
            y=alt.Y('Unique_Visitors:Q', title='Unique Visitors'),
            color=alt.Color('Unique_Visitors:Q', legend=None),  # Color bars based on Unique Visitors
            tooltip=['Product_Name:N', 'Unique_Visitors:Q']
        ).properties(width=600, height=300, title="Top N Most Popular Products by Unique Visitors")

        # Adding text labels on the bars
        product_text = product_chart.mark_text(
            align='center',
            baseline='middle',
            dy=-10,  # Adjust the vertical position of the text
            fontSize=12
        ).encode(
            text='Unique_Visitors:Q'
        )

        product_chart = product_chart + product_text  # Combine the bar chart with the text

        # Configure axis for readability
        product_chart = product_chart.configure_axis(
            labelAngle=90,  # Set x-labels to 0-degree angle
            labelFontSize=12,  # Increase font size of labels
            titleFontSize=16  # Increase font size of axis title
        )
        st.altair_chart(product_chart, use_container_width=True)

    # Top N most popular collections chart
    with chart_col2:
        # st.title('Most Popular Collections by Unique Visitors')
        add_tooltip_css()
        tooltip_html = render_tooltip(
        "This chart shows the top N most popular collections based on unique visitors. The x-axis represents the collection names, and the y-axis shows the number of unique visitors. Use the slider above to adjust the number of top collections displayed. Hover over the bars to see detailed information about each collection's unique visitors count.")
        st.markdown(f"<h1 style='display: inline-block;'>Most Popular collections by Unique Visitors {tooltip_html}</h1>",unsafe_allow_html=True)
        top_n_collections = st.slider("Select Top N Collections to Display", min_value=1, max_value=50, value=10)
        df_top_n_collection = df_collection_sorted.head(top_n_collections)
        st.markdown("<h3 style='text-align: center;'>Top N Most Popular Collections</h3>", unsafe_allow_html=True)

        collection_chart = alt.Chart(df_top_n_collection).mark_bar().encode(
            x=alt.X('Collection_Name:N', title='Collection Name', sort=df_top_n_collection['Unique_Visitors'].tolist(),
                    axis=alt.Axis(labelAngle=90)),
            y=alt.Y('Unique_Visitors:Q', title='Unique Visitors'),
            color=alt.Color('Unique_Visitors:Q', legend=None),  # Color bars based on Unique Visitors
            tooltip=['Collection_Name:N', 'Unique_Visitors:Q']
        ).properties(width=600, height=300, title="Top N Most Popular Collections by Unique Visitors")

        # Adding text labels on the bars
        collection_text = collection_chart.mark_text(
            align='center',
            baseline='middle',
            dy=-10,  # Adjust the vertical position of the text
            fontSize=12
        ).encode(
            text='Unique_Visitors:Q'
        )

        collection_chart = collection_chart + collection_text  # Combine the bar chart with the text

        # Configure axis for readability
        collection_chart = collection_chart.configure_axis(
            labelAngle=0,  # Set x-labels to 0-degree angle
            labelFontSize=14,  # Increase font size of labels
            titleFontSize=16  # Increase font size of axis title
        )
        st.altair_chart(collection_chart, use_container_width=True)

    #Todo-Product Name Most add to card in chart
    df_cart_add = df_cj[df_cj['Event'] == 'Cart Add']
    df_grouped_cart_add = df_cart_add.groupby('Product_Name')['Customer_IP'].nunique().reset_index()
    df_grouped_cart_add.rename(columns={'Customer_IP': 'Unique_Visitors'}, inplace=True)
    chart_col1, chart_col2 = st.columns(2)
    # Column 1: WordCloud for most searched terms
    with chart_col1:
        st.markdown("<h3 style='text-align: center;'>Most Searched Terms</h3>", unsafe_allow_html=True)
        search_terms = df_cj['Search_Term'].dropna().astype(str)  # Ensure there are no NaN values and all are strings
        search_term_counts = search_terms.value_counts()
        wordcloud = WordCloud(width=800, height=400, background_color='white').generate_from_frequencies(search_term_counts)
        image = wordcloud.to_image()
        image_stream = io.BytesIO()
        image.save(image_stream, format='PNG')
        image_stream.seek(0)
        st.image(image_stream, use_container_width=True)
    # Column 2: Bar chart for top added products to cart
    with chart_col2:
        # st.title('Most Added Products to Cart')
        add_tooltip_css()
        tooltip_html = render_tooltip(
            "This chart displays the top N products that were most frequently added to the cart, based on the number of unique visitors. The x-axis represents the product names, and the y-axis shows the count of unique visitors who added those products to their cart. Use the slider above to adjust the number of top products displayed. Hover over the bars to see detailed information about the number of unique visitors for each product.")
        st.markdown(
            f"<h1 style='display: inline-block;'>Most Added Products to Cart {tooltip_html}</h1>",
            unsafe_allow_html=True
        )
        top_n_products = st.slider("Select Top N Products to Display", min_value=10, max_value=50, value=10)
        st.markdown(f"<h3 style='text-align: center;'>Top {top_n_products} Most Added Products to Cart</h3>",unsafe_allow_html=True)
        # Adjust filtering logic to reflect slider value
        df_top_n_cart_add = df_grouped_cart_add.sort_values('Unique_Visitors', ascending=False).head(top_n_products)
        # Modify the color encoding to use Unique_Visitors for coloring the bars
        cart_add_chart = alt.Chart(df_top_n_cart_add).mark_bar().encode(
            x=alt.X('Product_Name:N', title='Product Name', sort=df_top_n_cart_add['Unique_Visitors'].tolist(),
                    axis=alt.Axis(labelAngle=90)),  # Rotate labels to 90 degrees for readability
            y=alt.Y('Unique_Visitors:Q', title='Unique Visitors'),
            color=alt.Color('Unique_Visitors:Q', legend=None),  # Color bars based on the Unique Visitors count
            tooltip=['Product_Name:N', 'Unique_Visitors:Q']
        ).properties(width=600, height=300, title="Top N Most Added Products to Cart by Unique Visitors")
        # Add labels on top of the bars (number of unique visitors)
        text = cart_add_chart.mark_text(
            align='center',
            baseline='middle',
            dy=-10,  # Adjust label position
            fontSize=12
        ).encode(
            text='Unique_Visitors:Q'
        )
        # Combine the bar chart and text labels
        cart_add_chart = cart_add_chart + text
        # Configure the axis for better readability
        cart_add_chart = cart_add_chart.configure_axis(
            labelAngle=0,  # Set the angle of the axis labels (x-axis) to 0 degrees
            labelFontSize=14,  # Increase font size of labels
            titleFontSize=16  # Increase font size of axis title
        )
        # Display the chart
        st.altair_chart(cart_add_chart, use_container_width=True)

    #Todo- Total add to cart product count
    col1 = st.columns(1)[0]
    df_cart_add = df_cj[df_cj['Event'] == 'Cart Add']
    df_grouped_cart_add = (
        df_cart_add.groupby('Product_Name')['Customer_IP']
        .nunique()
        .reset_index()
        .rename(columns={'Customer_IP': 'Unique_Visitors'})
    )
    total_unique_visitors = df_grouped_cart_add['Unique_Visitors'].sum()
    with col1:
        st.markdown(
            f"""
                <div class="card">
                    <p>Total added to cart products</p>
                    <h1>{total_unique_visitors}</h1>
                </div>
                """,
            unsafe_allow_html=True
        )

    #Todo- Total session with per day data
    col1 = st.columns(1)[0]
    with col1:
        # st.title('Total sessions: days of week')
        add_tooltip_css()
        tooltip_html = render_tooltip("This chart displays the total number of sessions across different days of the week. The pie chart shows how sessions are distributed by day, with each segment representing one day of the week. Hover 	over the segments to see the number of sessions for each specific day. The data is based on unique sessions for each customer IP.")
        st.markdown( f"<h1 style='display: inline-block;'>Total sessions: days of week {tooltip_html}</h1>",unsafe_allow_html=True)
        df_cj['Event_Time'] = pd.to_datetime(df_cj['Event_Time'], errors='coerce', utc=True)
        df_cj_ = df_cj.dropna(subset=['Event_Time'])
        df_cj['days_of_week'] = df_cj_['Event_Time'].dt.dayofweek.apply(
            lambda x: ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][x]
        )
        grouped_filtered_df = df_cj.groupby(['Customer_IP', 'session']).first().reset_index()
        day_count = grouped_filtered_df['days_of_week'].value_counts()
        day_count = day_count.reindex(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'], fill_value=0)
        pie_data = pd.DataFrame({
            'Day': day_count.index,
            'Count': day_count.values
        })
        pie_chart = alt.Chart(pie_data).mark_arc().encode(
            theta='Count:Q',
            color=alt.Color('Day:N', sort=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']),
            tooltip=['Day:N', 'Count:Q']
        ).properties(
            title="Total Sessions by Day of the Week"
        )
        st.altair_chart(pie_chart, use_container_width=True)
    #Todo-Session per hours---------------------------------------------
    col1 = st.columns(1)[0]
    with col1:
        # st.title('Total sessions: hours of day')
        add_tooltip_css()
        tooltip_html = render_tooltip(
            "This chart displays the total number of sessions by hour of the day. The line chart shows how sessions are distributed across different hours, with each point representing the number of sessions for 	a specific hour. Hover over the points or the line to see the number of sessions for each hour. The data is based on unique sessions for each customer IP, and the hours are shifted to a 1-24 range.")
        st.markdown(
            f"<h1 style='display: inline-block;'>Total sessions: hours of day {tooltip_html}</h1>",
            unsafe_allow_html=True
        )
        df_cj['Event_Time'] = pd.to_datetime(df_cj['Event_Time'], errors='coerce', utc=True)
        dyori_cj_df = df_cj.dropna(subset=['Event_Time'])
        dyori_cj_df['hour_of_day'] = dyori_cj_df['Event_Time'].dt.hour + 1  # Shift hours to 1-24 range
        grouped_filtered_df = dyori_cj_df.groupby(['Customer_IP', 'session']).first().reset_index()
        hour_count = grouped_filtered_df['hour_of_day'].value_counts().sort_index()
        hour_count = hour_count.reindex(range(1, 25), fill_value=0)
        hour_data = pd.DataFrame({
            'Hour of Day': hour_count.index,
            'Number of Sessions': hour_count.values
        })
        line_chart = alt.Chart(hour_data).mark_line().encode(
            x='Hour of Day:O',
            y='Number of Sessions:Q',
            tooltip=['Hour of Day:N', 'Number of Sessions:Q']
        ).properties(
            title="Total Sessions by Hour of the Day"
        )
        # Adding mark_point
        points = alt.Chart(hour_data).mark_point(size=60, color='red').encode(
            x='Hour of Day:O',
            y='Number of Sessions:Q',
            tooltip=['Hour of Day:N', 'Number of Sessions:Q']
        )
        # Combine line chart and points
        combined_chart = line_chart + points
        st.altair_chart(combined_chart, use_container_width=True)
    # Todo- Avg time spent on each page and Total time spent on each page
    df_cj['Time_On_Page'] = pd.to_numeric(df_cj['Time_On_Page'], errors='coerce')
    events = ['Cart', 'Home', 'Product', 'Collection']
    filtered_df = df_cj[df_cj['Event'].isin(events)]
    avg_time_per_event = filtered_df.groupby('Event')['Time_On_Page'].mean().reset_index()
    avg_time_per_event['Time_On_Page_Display'] = avg_time_per_event['Time_On_Page'].apply(convert_seconds)
    Total_time_spent = filtered_df.groupby('Event')['Time_On_Page'].sum().reset_index()
    Total_time_spent['Time_On_Page_Display'] = Total_time_spent['Time_On_Page'].apply(convert_seconds)
    col1, col2 = st.columns(2)
    with col1:
        # st.title('Average Time Spent on Each Event'
        add_tooltip_css()
        tooltip_html = render_tooltip("This pie chart displays the average time spent on each event (Cart, Home, Product, Collection). The size of each segment represents the average time spent on that event, and the color differentiates 	between event types. Hover over the segments to see the average time spent on each event, displayed in a human-readable format.")
        st.markdown(f"<h1 style='display: inline-block;'>Average Time Spent on Each Event {tooltip_html}</h1>",unsafe_allow_html=True)
        pie_chart_avg = alt.Chart(avg_time_per_event).mark_arc().encode(
            theta='Time_On_Page:Q',  # Use the original numeric value for the pie chart
            color='Event:N',  # Color by event type
            tooltip=['Event:N', 'Time_On_Page_Display:N']  # Display the converted time in tooltip
        ).properties(
            title="Average Time Spent on Each Event",
            width=350,
            height=350
        )
        st.altair_chart(pie_chart_avg, use_container_width=True)
    with col2:
        # st.title('Total Time Spent on Each Event')
        add_tooltip_css()
        tooltip_html = render_tooltip(
            "This pie chart shows the total time spent on each event (Cart, Home, Product, Collection). The size of each segment represents the total time spent on that event, and the color distinguishes between 	the different event types. Hover over the segments to view the total time spent on each event, displayed in a human-readable format.")

        st.markdown(
            f"<h1 style='display: inline-block;'>Total Time Spent on Each Event {tooltip_html}</h1>",
            unsafe_allow_html=True
        )
        pie_chart_total = alt.Chart(Total_time_spent).mark_arc().encode(
            theta='Time_On_Page:Q',  # Use the original numeric value for the pie chart
            color='Event:N',  # Color by event type
            tooltip=['Event:N', 'Time_On_Page_Display:N']  # Display the converted time in tooltip
        ).properties(
            title="Total Time Spent on Each Event",
            width=350,  # Set a fixed width for consistency
            height=350  # Set a fixed height for consistency
        )
        st.altair_chart(pie_chart_total, use_container_width=True)
    # Todo-Time_Spend on Each Product ID with Product Name------------------------------------------
    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        df_cj['Product_ID'] = df_cj['Product_ID'].astype(str).replace(".0", "", regex=True)
        time_spent_per_product = df_cj.groupby(['Product_ID', 'Product_Name'])['Time_On_Page'].sum().reset_index()
        time_spent_per_product_sorted = time_spent_per_product.sort_values(by='Time_On_Page', ascending=False)
        time_spent_per_product_sorted['Time_On_Page'] = time_spent_per_product_sorted['Time_On_Page'].apply(convert_seconds)
        # st.title("Summary of Total Time Spent Per Product")
        add_tooltip_css()
        tooltip_html = render_tooltip(
            "This table displays the total time spent on each product. The data is grouped by Product ID and Name, and the total time spent is calculated for each product. The table is sorted in descending 	order, showing the products that have the highest total time spent on top. Hover over the rows to see the time spent on each product, displayed in a human-readable format.")

        st.markdown(
            f"<h1 style='display: inline-block;'>Summary of Total Time Spent Per Product {tooltip_html}</h1>",
            unsafe_allow_html=True
        )
        st.markdown("### Total Time Spent on Each Product")
        st.dataframe(time_spent_per_product_sorted)
    with chart_col2:
        time_spent_per_product = df_cj.groupby([ 'Collection_Name'])['Time_On_Page'].sum().reset_index()
        time_spent_per_product_sorted = time_spent_per_product.sort_values(by='Time_On_Page', ascending=False)
        time_spent_per_product_sorted['Time_On_Page'] = time_spent_per_product_sorted['Time_On_Page'].apply(convert_seconds)
        # st.title("Summary of Total Time Spent Per Collections")
        add_tooltip_css()
        tooltip_html = render_tooltip(
            "This table displays the total time spent on each collection. The data is grouped by Collection Name, and the total time spent is calculated for each collection. The table is sorted in descending 	order, highlighting the collections with the most time spent. Hover over the rows to see the total time spent on each collection, displayed in a human-readable format.")

        st.markdown(
            f"<h1 style='display: inline-block;'>Summary of Total Time Spent Per Collections {tooltip_html}</h1>",
            unsafe_allow_html=True
        )
        st.markdown("### Total Time Spent on Each Collections")
        st.dataframe(time_spent_per_product_sorted)
    # Todo- Viewers On each Page---------------------------------------------------------------------------
    events = ['Cart', 'Home', 'Product', 'Collection']
    filtered_df = df_cj[df_cj['Event'].isin(events)]
    viewer_counts = filtered_df.groupby("Event")["Customer_IP"].nunique().reset_index()
    viewer_counts.columns = ["Event", "Total Viewers"]
    # Streamlit layout for charts
    chart_col1, chart_col2 = st.columns(2)
    # Viewers by Event chart
    with chart_col1:
        # st.title("Total Viewers on Each Page")
        add_tooltip_css()
        tooltip_html = render_tooltip(
            "This bar chart displays the total number of viewers for each page or event. The x-axis represents the different pages or events, and the y-axis shows the total viewers count. Hover over the bars to 	see the exact number of viewers for each page/event. The bars are color-coded based on the total viewers count to give a visual cue of viewer distribution.")
        st.markdown(f"<h1 style='display: inline-block;'>Total Viewers on Each Page {tooltip_html}</h1>",unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center;'>Viewers by Page</h3>", unsafe_allow_html=True)
        # Modify the color encoding to use 'Total Viewers' for coloring the bars
        page_chart = alt.Chart(viewer_counts).mark_bar().encode(
            x=alt.X('Event:N', title='Page/Event', sort=viewer_counts['Event'].tolist()),
            y=alt.Y('Total Viewers:Q', title='Total Viewers'),
            color=alt.Color('Total Viewers:Q', legend=None),  # Color bars based on the 'Total Viewers' count
            tooltip=['Event:N', 'Total Viewers:Q']
        ).properties(width=600, height=300, title="Viewers by Page")
        # Add labels on top of the bars (Total Viewers count)
        page_text = page_chart.mark_text(
            align='center',
            baseline='middle',
            dy=-10,  # Adjust label position
            fontSize=12
        ).encode(
            text='Total Viewers:Q'
        )
        # Combine the bar chart and text labels
        page_chart = page_chart + page_text
        # Configure the axis for better readability
        page_chart = page_chart.configure_axis(
            labelAngle=0,  # Set the angle of the axis labels (x-axis) to 0 degrees
            labelFontSize=14,  # Increase font size of labels
            titleFontSize=16  # Increase font size of axis title
        )
        # Display the chart
        st.altair_chart(page_chart, use_container_width=True)

    #Todo -Bounce Rate of each Customer who spend time less then 30 second
    customer_time = df_cj.groupby('Customer_IP')['Time_On_Page'].sum().reset_index()
    filtered_customer_time = customer_time[customer_time['Time_On_Page'] < 30]
    total_customers = customer_time['Customer_IP'].nunique()
    customers_under_30_seconds = filtered_customer_time['Customer_IP'].nunique()
    percentage = (customers_under_30_seconds / total_customers) * 100
    percentage=round(percentage,2)
    with chart_col2:
        st.title("Customers Rate Under 30 Second")
        st.markdown(
            f"""
                       <div class="card">
                           <p>Bounce rate in percentage</p>
                           <h1>{percentage}%</h1>
                       </div>
                       """,
            unsafe_allow_html=True
        )
    #Todo -Bounce Rate By Event type
    events = ['Cart', 'Home', 'Product', 'Collection']
    filtered_df = df_cj[df_cj['Event'].isin(events)]
    filtered_df = filtered_df.sort_values(by=['Customer_IP', 'session'], ascending=True)
    last_session_df = filtered_df.drop_duplicates(subset=['Customer_IP', 'session'], keep='last')
    bounce_df = last_session_df[last_session_df['Time_On_Page'] < 10]
    bounce_rate_by_event = {}
    for event in events:
        # Get unique Customer_IPs for each event type
        total_events_event_count = df_cj[df_cj['Event'] == event]['Customer_IP'].nunique()
        bounce_events_event_count = bounce_df[bounce_df['Event'] == event]['Customer_IP'].nunique()
        bounce_rate_percentage = (bounce_events_event_count / total_events_event_count) * 100 if total_events_event_count > 0 else 0
        bounce_rate_by_event[event] = bounce_rate_percentage
    # Convert the bounce rates dictionary to a DataFrame for Altair
    bounce_rate_df = pd.DataFrame(list(bounce_rate_by_event.items()), columns=['Event', 'Bounce Rate'])
    # Round the 'Bounce Rate' to 2 decimal places
    bounce_rate_df['Bounce Rate'] = bounce_rate_df['Bounce Rate'].round(2)
    # Streamlit layout with chart column
    chart_col1, _ = st.columns(2)
    with chart_col1:
        # st.title("Bounce Rate(%) by Event Type")
        add_tooltip_css()
        tooltip_html = render_tooltip("This bar chart shows the bounce rate percentage for each event type. The x-axis represents different event types, and the y-axis shows the bounce rate for each event, displayed as a percentage. Hover 	over the bars to view the exact bounce rate percentage for each event type. The bars are color-coded based on the bounce rate, providing a visual indication of the bounce rate distribution across event types.")
        st.markdown(f"<h1 style='display: inline-block;'>Bounce Rate(%) by Event Type {tooltip_html}</h1>",unsafe_allow_html=True)
        # st.markdown("<h3 style='text-align: center;'>Bounce Rates for Each Event</h3>", unsafe_allow_html=True)
        # Create the Altair chart
        bounce_chart = alt.Chart(bounce_rate_df).mark_bar().encode(
            x=alt.X('Event:N', title='Event Type', sort=bounce_rate_df['Event'].tolist()),
            y=alt.Y('Bounce Rate:Q', title='Bounce Rate (%)'),
            color=alt.Color('Bounce Rate:Q', legend=None),  # Color bars based on Bounce Rate percentage
            tooltip=['Event:N', 'Bounce Rate:Q']
        ).properties(width=600, height=300, title="Bounce Rate by Event Type")
        # Add text labels to the bars (Bounce Rate percentage)
        bounce_text = bounce_chart.mark_text(
            align='center',
            baseline='middle',
            dy=-10,  # Adjust label position
            fontSize=12
        ).encode(
            text='Bounce Rate:Q'
        )
        # Combine the bar chart and text labels
        bounce_chart = bounce_chart + bounce_text
        # Configure the axis for better readability
        bounce_chart = bounce_chart.configure_axis(
            labelAngle=0,  # Set the angle of the axis labels (x-axis) to 0 degrees
            labelFontSize=14,  # Increase font size of labels
            titleFontSize=16  # Increase font size of axis title
        )
        # Display the chart
        st.altair_chart(bounce_chart)

def show_order_data_page():
    st.title('Order Data')
    add_custom_css()
    # Todo- Card Creation for the above
    col1  = st.columns(1)[0]
    with col1:
        total_listed_customers = df_orders['Order_ID'].nunique()
        st.markdown(
            f"""
                <div class="card">
                    <p>Total orders placed</p>
                    <h1>{total_listed_customers}</h1>
                </div>
                """,
            unsafe_allow_html=True
        )
    st.title("Preview Filtered Order Data")
    st.subheader("Customer Order Data")
    filtered_orders = filter_by_date(df_orders, 'Order_Created_At')
    # with st.expander("Preview Filtered Orders Data"):
    st.dataframe(filtered_orders)

    # Group by 'Order_ID' and aggregate the 'Order_Created_At' column
    df_orders_ = df_orders.groupby('Order_ID').agg({'Order_Created_At': 'first'})
    # Ensure the 'Order_Created_At' column is in datetime format
    df_orders_['Order_Created_At'] = pd.to_datetime(df_orders_['Order_Created_At'], errors='coerce', utc=True)
    # Add a new column for Weekday/Weekend
    df_orders_['Weekday_Weekend'] = df_orders_['Order_Created_At'].dt.dayofweek.apply(
        lambda x: 'Weekend' if x >= 5 else 'Weekday'
    )
    # Calculate the count of orders on weekdays and weekends
    weekday_count = df_orders_[df_orders_['Weekday_Weekend'] == 'Weekday'].shape[0]
    weekend_count = df_orders_[df_orders_['Weekday_Weekend'] == 'Weekend'].shape[0]
    # Prepare data for pie chart
    counts = [weekday_count, weekend_count]
    labels = ['Weekday', 'Weekend']
    pie_data = pd.DataFrame({
        'Category': labels,
        'Count': counts,
        'Percentage': [(count / sum(counts)) * 100 for count in counts]  # Calculate percentage
    })
    pie_data['Label'] = pie_data['Percentage'].round(1).astype(str) + '%'

    # Create pie chart using Altair
    pie_chart = alt.Chart(pie_data).mark_arc().encode(
        theta=alt.Theta(field="Count", type="quantitative"),
        color=alt.Color(field="Category", type="nominal"),
        tooltip=["Category", "Count", "Percentage"],  # Show both count and percentage in tooltip
    )

    # Display the result in Streamlit
    col1 = st.columns(1)[0]
    with col1:
        st.write(f"Weekday Count: {weekday_count} ({(weekday_count / sum(counts)) * 100:.2f}%)")
        st.write(f"Weekend Count: {weekend_count} ({(weekend_count / sum(counts)) * 100:.2f}%)")
        st.title('Total orders placed: Weekday vs Weekend')
        st.markdown("<h3 style='text-align: center;'>Orders by Weekday/Weekend</h3>", unsafe_allow_html=True)
        st.altair_chart(pie_chart, use_container_width=True)

    # Todo-Total Order placed on days on weeks------
    # Group by 'Order_ID' and aggregate the 'Order_Created_At' column
    df_orders_ = df_orders.groupby('Order_ID').agg({'Order_Created_At': 'first'}).reset_index()
    # Convert 'Order_Created_At' to datetime format if not already done
    df_orders_['Order_Created_At'] = pd.to_datetime(df_orders_['Order_Created_At'], errors='coerce', utc=True)
    # Proceed with the rest of your code
    col2 = st.columns(1)[0]
    with col2:
        # Add the 'days_of_week' column to the df_orders_ DataFrame (after grouping)
        df_orders_['days_of_week'] = df_orders_['Order_Created_At'].dt.dayofweek.apply(
            lambda x: ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][x]
        )
        # Count occurrences of each day
        day_count = df_orders_['days_of_week'].value_counts()
        # Reorder the days of the week
        day_count = day_count.reindex(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'],fill_value=0)
        # Create a DataFrame for pie chart
        pie_data = pd.DataFrame({
            'Day': day_count.index,
            'Count': day_count.values
        })
        # Create the pie chart
        pie_chart = alt.Chart(pie_data).mark_arc().encode(
            theta=alt.Theta(field="Count", type="quantitative"),
            color=alt.Color(field="Day", type="nominal",sort=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']),
            tooltip=["Day:N", "Count:Q"]
        )
        # Display results in Streamlit
        st.title('Total Orders Placed: Days of the Week')
        st.markdown("<h3 style='text-align: center;'>Orders by Day of the Week</h3>", unsafe_allow_html=True)
        st.altair_chart(pie_chart, use_container_width=True)

    #Todo-Total Orders Placed: Hours of the Day
    # Group by 'Order_ID' and aggregate 'Order_Created_At' to get the first occurrence
    df_orders_ = df_orders.groupby('Order_ID').agg({'Order_Created_At': 'first'}).reset_index()
    # Convert 'Order_Created_At' to datetime if not already done
    df_orders_['Order_Created_At'] = pd.to_datetime(df_orders_['Order_Created_At'], errors='coerce', utc=True)
    col1 = st.columns(1)[0]
    with col1:
        # Add 'hour_of_day' column for the df_orders_ DataFrame
        df_orders_['hour_of_day'] = df_orders_['Order_Created_At'].dt.hour + 1  # Shift hours to 1-24 range
        # Count orders per hour
        hour_count = df_orders_['hour_of_day'].value_counts().sort_index()
        # Reindex to ensure every hour from 1 to 24 is included
        hour_count = hour_count.reindex(range(1, 25), fill_value=0)
        # Prepare data for the chart
        hour_data = pd.DataFrame({
            'Hour of Day': hour_count.index,
            'Number of Orders': hour_count.values
        })
        # Display the title and description
        st.title('Total Orders Placed: Hours of the Day')
        st.markdown("<h3 style='text-align: center;'>Orders by Hour of the Day</h3>", unsafe_allow_html=True)
        line_chart = alt.Chart(hour_data).mark_line().encode(
            x=alt.X('Hour of Day:O', title='Hour of Day', scale=alt.Scale(domain=list(range(1, 25)))),
            y=alt.Y('Number of Orders:Q', title='Number of Orders'),
            tooltip=['Hour of Day', 'Number of Orders']
        ).properties(
            width=700,
            height=400
        )
        # Add points to the line chart
        points = alt.Chart(hour_data).mark_point(size=100, color='red').encode(
            x=alt.X('Hour of Day:O', title='Hour of Day'),
            y=alt.Y('Number of Orders:Q', title='Number of Orders'),
            tooltip=['Hour of Day', 'Number of Orders']
        )

        # Combine the line chart and points
        combined_chart = line_chart + points
        st.altair_chart(combined_chart, use_container_width=True)

    #Todo-Total orders placed: day, month, quarter, year
    df_orders_ = df_orders.groupby('Order_ID').agg({'Order_Created_At': 'first'}).reset_index()
    # Convert 'Order_Created_At' to datetime if not already done
    df_orders_['Order_Created_At'] = pd.to_datetime(df_orders_['Order_Created_At'], errors='coerce', utc=True)
    col1 = st.columns(1)[0]
    with col1:
        # Extract the day, month, quarter, and year from 'Order_Created_At'
        df_orders_['day'] = df_orders_['Order_Created_At'].dt.date
        # Calculate total orders placed per day
        orders_per_day = df_orders_.groupby('day').size().reset_index(name='order_count')
        # Create a complete date range
        start_date = orders_per_day['day'].min()
        end_date = datetime.today().date()
        full_date_range = pd.date_range(start=start_date, end=end_date)
        # Reindex `orders_per_day` to ensure all dates are included
        orders_per_day.set_index('day', inplace=True)
        orders_per_day = orders_per_day.reindex(full_date_range, fill_value=0).reset_index()
        orders_per_day.rename(columns={'index': 'day'}, inplace=True)
        # Add 'month', 'quarter', and 'year' columns
        orders_per_day['month'] = orders_per_day['day'].dt.to_period('M').astype(str)  # Year-Month format
        orders_per_day['quarter'] = orders_per_day['day'].dt.to_period('Q').astype(str)  # Year-Quarter format
        orders_per_day['year'] = orders_per_day['day'].dt.year  # Year format
        # Group data-----
        orders_per_month = orders_per_day.groupby('month')['order_count'].sum().reset_index()
        orders_per_month['month'] = pd.to_datetime(orders_per_month['month'], format='%Y-%m')
        orders_per_month = orders_per_month.sort_values(by='month')
        orders_per_quarter = orders_per_day.groupby('quarter')['order_count'].sum().reset_index()
        orders_per_year = orders_per_day.groupby('year')['order_count'].sum().reset_index()
        # Streamlit Visualization
        st.title('Order Count Visualizations')
        view = st.radio("Select View", ['Orders per Day', 'Orders per Month', 'Orders per Quarter', 'Orders per Year'])
        if view == 'Orders per Day':
            st.title('Orders Placed: Days')
            st.markdown("<h3 style='text-align: center;'>Orders by Day</h3>", unsafe_allow_html=True)
            line_chart = alt.Chart(orders_per_day).mark_line().encode(
                x=alt.X('day:T', title='Date',
                        axis=alt.Axis(format="%b %d, %Y", labelAngle=-90, tickMinStep=1)),
                y=alt.Y('order_count:Q', title='Number of Orders'),
                tooltip=['day:T', 'order_count:Q']
            )
            points = alt.Chart(orders_per_day).mark_point(size=60, color='red').encode(
                x='day:T',
                y='order_count:Q',
                tooltip=['day:T', 'order_count:Q']
            )
            combined_chart = line_chart + points
            st.altair_chart(combined_chart, use_container_width=True)
        elif view == 'Orders per Month':
            st.title('Orders Placed: Months')
            st.markdown("<h3 style='text-align: center;'>Orders by Month</h3>", unsafe_allow_html=True)
            # Ensure that the month column is formatted as 'Month Year'
            orders_per_month['month'] = orders_per_month['month'].dt.strftime('%b %Y')  # Convert to Month Year format
            # Create the chart with the properly formatted month labels
            line_chart = alt.Chart(orders_per_month).mark_line().encode(
                x=alt.X('month:O', title='Month', axis=alt.Axis(labelAngle=-45)),  # Ordinal scale for months
                y=alt.Y('order_count:Q', title='Number of Orders'),
                tooltip=[alt.Tooltip('month:N', title='Month'), 'order_count:Q']
            )
            points = alt.Chart(orders_per_month).mark_point(size=60, color='red').encode(
                x=alt.X('month:O', title='Month'),
                y=alt.Y('order_count:Q', title='Number of Orders'),
                tooltip=[alt.Tooltip('month:N', title='Month'), 'order_count:Q']
            )
            combined_chart = line_chart + points
            st.altair_chart(combined_chart, use_container_width=True)

        elif view == 'Orders per Quarter':
            st.title('Orders Placed: Quarters')
            st.markdown("<h3 style='text-align: center;'>Orders by Quarter</h3>", unsafe_allow_html=True)
            line_chart = alt.Chart(orders_per_quarter).mark_line().encode(
                x=alt.X('quarter:N', title='Quarter'),
                y=alt.Y('order_count:Q', title='Number of Orders'),
                tooltip=['quarter:N', 'order_count:Q']
            )
            points = alt.Chart(orders_per_quarter).mark_point(size=60, color='red').encode(
                x='quarter:N',
                y='order_count:Q',
                tooltip=['quarter:N', 'order_count:Q']
            )
            combined_chart = line_chart + points
            st.altair_chart(combined_chart, use_container_width=True)

        elif view == 'Orders per Year':
            st.title('Orders Placed: Years')
            st.markdown("<h3 style='text-align: center;'>Orders by Year</h3>", unsafe_allow_html=True)
            line_chart = alt.Chart(orders_per_year).mark_line().encode(
                x=alt.X('year:O', title='Year'),
                y=alt.Y('order_count:Q', title='Number of Orders'),
                tooltip=['year:O', 'order_count:Q']
            )
            points = alt.Chart(orders_per_year).mark_point(size=60, color='red').encode(
                x='year:O',
                y='order_count:Q',
                tooltip=['year:O', 'order_count:Q']
            )
            combined_chart = line_chart + points
            st.altair_chart(combined_chart, use_container_width=True)

    #Todo-average_orders_per_customer----------------------------------------------------------
    orders_per_customer = df_orders.groupby('Customer_ID')['Order_ID'].nunique().reset_index()
    average_orders_per_customer = orders_per_customer['Order_ID'].mean()
    average_orders_per_customer = round(average_orders_per_customer, 2)
    #Todo -Total Order canceled count--------------------------------------------------
    total_canceled_orders = df_orders[df_orders['Order_Cancelled_At'].notna()].shape[0]
    #Todo-Most orders placed by a customer-----------------------------------------------
    customer_order_counts = df_orders.groupby('Customer_ID')['Order_ID'].nunique()
    max_orders = customer_order_counts.max()
    #Todo-Average-order valued-----------------------------------------------------------
    order_data = df_orders.groupby('Order_ID').agg({'Order_Total_Price': 'first'}).reset_index()
    average_order_value = order_data['Order_Total_Price'].mean()
    average_order_value = round(average_order_value, 2)
    col1,col2,col3,col4=st.columns(4)
    with col1:
        st.markdown(
            f"""
                <div class="card">
                    <p>Average orders per customer</p>
                    <h1>{average_orders_per_customer}</h1>
                </div>
                """,
            unsafe_allow_html=True
        )
    with col2:
        st.markdown(
            f"""
                <div class="card">
                    <p>Total orders cancelled</p>
                    <h1>{total_canceled_orders}</h1>
                </div>
                """,
            unsafe_allow_html=True
        )
    with col3:
        st.markdown(
            f"""
                <div class="card">
                    <p>Most orders placed by a customer</p>
                    <h1>{max_orders}</h1>
                </div>
                """,
            unsafe_allow_html=True
        )
    with col4:
        st.markdown(
            f"""
                <div class="card">
                    <p>Average order value</p>
                    <h1>{average_order_value}</h1>
                </div>
                """,
            unsafe_allow_html=True
        )
    #Todo-Highest valued orders and Least valued orders-------------------------------------
    order_data = df_orders.groupby('Customer_Name').agg(
        {'Order_ID': 'first', 'Order_Total_Price': 'first'}).reset_index()
    order_data = order_data.dropna(subset=['Order_ID'])
    top_customers = order_data.nlargest(50, 'Order_Total_Price')
    least_customers = order_data.nsmallest(50, 'Order_Total_Price')
    chart_col1, chart_col2 = st.columns(2)

    # Chart for Top N Customers
    with chart_col1:
        st.title('Highest valued orders')
        top_n = st.slider("Select Top N Customers to Display", min_value=1, max_value=50, value=5, key="top_n_largest")
        top_customers_filtered = top_customers.nlargest(top_n, 'Order_Total_Price')
        st.markdown("<h3 style='text-align: center;'>Top N Customers by Total Order Price</h3>", unsafe_allow_html=True)
        # Create bar chart for Top N Customers
        top_chart = alt.Chart(top_customers_filtered).mark_bar().encode(
            x=alt.X('Customer_Name:O', title='Customer Name',sort=top_customers_filtered['Order_Total_Price'].tolist()),
            # Customer_Name on X-axis
            y=alt.Y('Order_Total_Price:Q', title='Total Order Price (€)'),  # Order_Total_Price on Y-axis
            color=alt.Color('Order_Total_Price:Q', legend=None),  # Color bars by Order_Total_Price
            tooltip=['Customer_Name:N',alt.Tooltip('Order_Total_Price:Q', title='Total Order Price (€)', format=".2f")]
        ).properties(width=350, height=300)
        # Add text on bars
        top_chart_text = top_chart.mark_text(
            align='center',
            baseline='middle',
            dy=-10,  # Adjust text position
            fontSize=12
        ).encode(
            text=alt.Text('Order_Total_Price:Q', format=".2f")  # Add € symbol and format to 2 decimal places
        )
        top_chart = top_chart + top_chart_text
        top_chart = top_chart.configure_axis(
            labelAngle=0,
            labelFontSize=14,
            titleFontSize=16
        )
        st.altair_chart(top_chart, use_container_width=True)

    # Chart for Least N Customers
    with chart_col2:
        st.title("Least valued orders")
        least_n = st.slider("Select Least N Customers to Display", min_value=1, max_value=50, value=5,
                            key="top_n_smallest")
        least_customers_filtered = least_customers.nsmallest(least_n, 'Order_Total_Price')
        st.markdown("<h3 style='text-align: center;'>Least N Customers by Total Order Price</h3>",
                    unsafe_allow_html=True)
        # Create bar chart for Least N Customers
        least_chart = alt.Chart(least_customers_filtered).mark_bar().encode(
            x=alt.X('Customer_Name:O', title='Customer Name',sort=least_customers_filtered['Order_Total_Price'].tolist()),
            # Customer_Name on X-axis
            y=alt.Y('Order_Total_Price:Q', title='Total Order Price (€)'),  # Order_Total_Price on Y-axis
            color=alt.Color('Order_Total_Price:Q', legend=None),  # Color bars by Order_Total_Price
            tooltip=['Customer_Name:N',alt.Tooltip('Order_Total_Price:Q', title='Total Order Price (€)', format=".2f")]
        ).properties(width=350, height=300)
        # Add text on bars
        least_chart_text = least_chart.mark_text(
            align='center',
            baseline='middle',
            dy=-10,  # Adjust text position
            fontSize=12
        ).encode(
            text=alt.Text('Order_Total_Price:Q', format=".2f")  # Add € symbol and format to 2 decimal places
        )
        least_chart = least_chart + least_chart_text
        least_chart = least_chart.configure_axis(
            labelAngle=0,
            labelFontSize=14,
            titleFontSize=16
        )
        st.altair_chart(least_chart, use_container_width=True)

    #Todo-Total Order by Referring Site
    df_unique_orders = df_orders.drop_duplicates(subset="Order_ID", keep="first")
    # Step 2: Calculate total orders by referring sites
    total_orders_by_site = df_unique_orders.groupby("Order_Referring_Site")["Order_ID"].count().reset_index()
    total_orders_by_site.columns = ["Referring Site", "Total Orders"]
    # Step 3: Streamlit layout
    st.title("Total Orders by Referring Sites")
    st.markdown("### Visualizing the count of total orders grouped by referring sites")
    # Slider for selecting top N referring sites
    top_n = st.slider("Select Top N Referring Sites to Display", min_value=1, max_value=len(total_orders_by_site),value=5)
    # Filtering for top N referring sites
    top_order_sites = total_orders_by_site.nlargest(top_n, "Total Orders")
    # Step 4: Create Altair Chart
    chart = alt.Chart(top_order_sites).mark_bar().encode(
        x=alt.X("Referring Site:O", title="Referring Site", sort="-y"),
        y=alt.Y("Total Orders:Q", title="Number of Orders"),
        color=alt.Color("Total Orders:Q", legend=None),
        tooltip=["Referring Site:N", "Total Orders:Q"]
    ).properties(
        width=700,
        height=400,
        title="Top N Referring Sites by Total Orders"
    )
    # Adding text labels on the bars
    text = chart.mark_text(
        align="center",
        baseline="middle",
        dy=-10  # Adjust text position
    ).encode(
        text="Total Orders:Q"
    )
    # Combine chart and text
    final_chart = chart + text
    # Configure axis and chart aesthetics
    final_chart = final_chart.configure_axis(
        labelAngle=0,
        labelFontSize=12,
        titleFontSize=14
    )
    # Display the chart
    st.altair_chart(final_chart, use_container_width=True)

def show_abandoned_checkouts_page():
    st.title('Abandoned Checkouts')
    add_custom_css()
    # Todo- Card Creation for the above
    col1 = st.columns(1)[0]
    with col1:
        abandoned_orders = df_abandoned_checkouts['Order_ID'].nunique()
        st.markdown(
            f"""
                <div class="card">
                    <p>Total abandoned orders</p>
                    <h1>{abandoned_orders}</h1>
                </div>
                """,
            unsafe_allow_html=True
        )
    st.title("Preview Filtered Abandoned Checkouts Data")
    st.subheader("Abandoned Checkouts Data")
    filtered_abandoned_checkouts = filter_by_date(df_abandoned_checkouts, 'Order_Created_At')
    # with st.expander("Preview Filtered Abandoned Checkouts Data"):
    st.dataframe(filtered_abandoned_checkouts)
    # Todo-Total Order placed on weekdays and weekend
    # Group by 'Order_ID' and aggregate the 'Order_Created_At' column
    df_abandoned_checkouts_ = df_abandoned_checkouts.groupby('Order_ID').agg({'Order_Created_At': 'first'})
    # Ensure the 'Order_Created_At' column is in datetime format
    df_abandoned_checkouts_['Order_Created_At'] = pd.to_datetime(df_abandoned_checkouts_['Order_Created_At'],errors='coerce', utc=True)
    # Add a new column for Weekday/Weekend
    df_abandoned_checkouts_['Weekday_Weekend'] = df_abandoned_checkouts_['Order_Created_At'].dt.dayofweek.apply(
        lambda x: 'Weekend' if x >= 5 else 'Weekday'
    )
    # Calculate the count of orders on weekdays and weekends
    weekday_count = df_abandoned_checkouts_[df_abandoned_checkouts_['Weekday_Weekend'] == 'Weekday'].shape[0]
    weekend_count = df_abandoned_checkouts_[df_abandoned_checkouts_['Weekday_Weekend'] == 'Weekend'].shape[0]
    # Prepare data for pie chart
    counts = [weekday_count, weekend_count]
    labels = ['Weekday', 'Weekend']
    pie_data = pd.DataFrame({
        'Category': labels,
        'Count': counts,
        'Percentage': [(count / sum(counts)) * 100 for count in counts]  # Calculate percentage
    })
    pie_data['Label'] = pie_data['Percentage'].round(1).astype(str) + '%'
    # Create pie chart using Altair
    pie_chart = alt.Chart(pie_data).mark_arc().encode(
        theta=alt.Theta(field="Count", type="quantitative"),
        color=alt.Color(field="Category", type="nominal"),
        tooltip=["Category", "Count", "Percentage"],  # Show both count and percentage in tooltip
    )
    # Display the result in Streamlit
    col1 = st.columns(1)[0]
    with col1:
        st.write(f"Weekday Count: {weekday_count} ({(weekday_count / sum(counts)) * 100:.2f}%)")
        st.write(f"Weekend Count: {weekend_count} ({(weekend_count / sum(counts)) * 100:.2f}%)")
        st.title('Total orders abandoned: weekday vs weekend')
        st.markdown("<h3 style='text-align: center;'>Orders abandoned by Weekday/Weekend</h3>", unsafe_allow_html=True)
        st.altair_chart(pie_chart, use_container_width=True)

    #Todo----------Total orders abandoned: days of week-------------------
    # Group by 'Order_ID' and aggregate the 'Order_Created_At' column
    df_abandoned_checkouts_ = df_abandoned_checkouts.groupby('Order_ID').agg(
        {'Order_Created_At': 'first'}).reset_index()
    # Convert 'Order_Created_At' to datetime format if not already done
    df_abandoned_checkouts_['Order_Created_At'] = pd.to_datetime(df_abandoned_checkouts_['Order_Created_At'],errors='coerce', utc=True)
    # Proceed with the rest of your code
    col2 = st.columns(1)[0]
    with col2:
        # Add the 'days_of_week' column to the df_abandoned_checkouts_ DataFrame (after grouping)
        df_abandoned_checkouts_['days_of_week'] = df_abandoned_checkouts_['Order_Created_At'].dt.dayofweek.apply(
            lambda x: ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][x]
        )
        # Count occurrences of each day
        day_count = df_abandoned_checkouts_['days_of_week'].value_counts()
        # Reorder the days of the week
        day_count = day_count.reindex(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'],
                                      fill_value=0)
        # Create a DataFrame for pie chart
        pie_data = pd.DataFrame({
            'Day': day_count.index,
            'Count': day_count.values
        })
        # Create the pie chart
        pie_chart = alt.Chart(pie_data).mark_arc().encode(
            theta=alt.Theta(field="Count", type="quantitative"),
            color=alt.Color(field="Day", type="nominal",
                            sort=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']),
            tooltip=["Day:N", "Count:Q"]
        )
        # Display results in Streamlit
        st.title('Total orders abandoned: days of week')
        st.markdown("<h3 style='text-align: center;'>Orders abandoned by Day of the Week</h3>", unsafe_allow_html=True)
        st.altair_chart(pie_chart, use_container_width=True)
    #Todo- Total orders abandoned: hours of day
    df_abandoned_checkouts_ = df_abandoned_checkouts.groupby('Order_ID').agg(
        {'Order_Created_At': 'first'}).reset_index()
    # Convert 'Order_Created_At' to datetime if not already done
    df_abandoned_checkouts_['Order_Created_At'] = pd.to_datetime(df_abandoned_checkouts_['Order_Created_At'],errors='coerce', utc=True)
    col1 = st.columns(1)[0]
    with col1:
        # Add 'hour_of_day' column for the df_abandoned_checkouts_ DataFrame
        df_abandoned_checkouts_['hour_of_day'] = df_abandoned_checkouts_['Order_Created_At'].dt.hour + 1  # Shift hours to 1-24 range
        # Count orders per hour
        hour_count = df_abandoned_checkouts_['hour_of_day'].value_counts().sort_index()
        # Reindex to ensure every hour from 1 to 24 is included
        hour_count = hour_count.reindex(range(1, 25), fill_value=0)
        # Prepare data for the chart
        hour_data = pd.DataFrame({
            'Hour of Day': hour_count.index,
            'Number of Orders': hour_count.values
        })
        # Display the title and description
        st.title('Total orders abandoned: hours of day')
        st.markdown("<h3 style='text-align: center;'>Orders abandoned by Hour of the Day</h3>", unsafe_allow_html=True)
        line_chart = alt.Chart(hour_data).mark_line().encode(
            x=alt.X('Hour of Day:O', title='Hour of Day', scale=alt.Scale(domain=list(range(1, 25)))),
            y=alt.Y('Number of Orders:Q', title='Number of Orders'),
            tooltip=['Hour of Day', 'Number of Orders']
        ).properties(
            width=700,
            height=400
        )
        # Add points to the line chart
        points = alt.Chart(hour_data).mark_point(size=100, color='red').encode(
            x=alt.X('Hour of Day:O', title='Hour of Day'),
            y=alt.Y('Number of Orders:Q', title='Number of Orders'),
            tooltip=['Hour of Day', 'Number of Orders']
        )
        # Combine the line chart and points
        combined_chart = line_chart + points
        st.altair_chart(combined_chart, use_container_width=True)
    #Todo-Total orders abandoned: day, month, quarter, year
    # Group by 'Order_ID' and aggregate 'Order_Created_At' to get the first occurrence in abandoned checkouts
    df_abandoned_checkouts_ = df_abandoned_checkouts.groupby('Order_ID').agg({'Order_Created_At': 'first'}).reset_index()
    # Convert 'Order_Created_At' to datetime if not already done for abandoned checkouts
    df_abandoned_checkouts_['Order_Created_At'] = pd.to_datetime(df_abandoned_checkouts_['Order_Created_At'],errors='coerce', utc=True)
    col1 = st.columns(1)[0]
    with col1:
        # Extract the day, month, quarter, and year from 'Order_Created_At'
        df_abandoned_checkouts_['day'] = df_abandoned_checkouts_['Order_Created_At'].dt.date
        # Calculate total abandoned orders placed per day
        abandoned_orders_per_day = df_abandoned_checkouts_.groupby('day').size().reset_index(name='order_count')
        # Create a complete date range for abandoned orders
        start_date = abandoned_orders_per_day['day'].min()
        end_date = datetime.today().date()
        full_date_range = pd.date_range(start=start_date, end=end_date)
        # Reindex `abandoned_orders_per_day` to ensure all dates are included
        abandoned_orders_per_day.set_index('day', inplace=True)
        abandoned_orders_per_day = abandoned_orders_per_day.reindex(full_date_range, fill_value=0).reset_index()
        abandoned_orders_per_day.rename(columns={'index': 'day'}, inplace=True)
        # Add 'month', 'quarter', and 'year' columns
        abandoned_orders_per_day['month'] = abandoned_orders_per_day['day'].dt.to_period('M').astype(str)  # Year-Month format
        abandoned_orders_per_day['quarter'] = abandoned_orders_per_day['day'].dt.to_period('Q').astype(str)  # Year-Quarter format
        abandoned_orders_per_day['year'] = abandoned_orders_per_day['day'].dt.year  # Year format
        # Group data for abandoned orders
        abandoned_orders_per_month = abandoned_orders_per_day.groupby('month')['order_count'].sum().reset_index()
        abandoned_orders_per_month['month'] = pd.to_datetime(abandoned_orders_per_month['month'], format='%Y-%m')
        abandoned_orders_per_month = abandoned_orders_per_month.sort_values(by='month')
        #Group data for Quarter data set
        abandoned_orders_per_quarter = abandoned_orders_per_day.groupby('quarter')['order_count'].sum().reset_index()
        #group data for year dataset
        abandoned_orders_per_year = abandoned_orders_per_day.groupby('year')['order_count'].sum().reset_index()
        # Streamlit Visualization for abandoned orders
        st.title('Abandoned Order Count Visualizations')
        view = st.radio("Select View",['Abandoned Orders per Day', 'Abandoned Orders per Month', 'Abandoned Orders per Quarter','Abandoned Orders per Year'])
        if view == 'Abandoned Orders per Day':
            st.title('Abandoned Orders: Days')
            st.markdown("<h3 style='text-align: center;'>Abandoned Orders by Day</h3>", unsafe_allow_html=True)
            line_chart = alt.Chart(abandoned_orders_per_day).mark_line().encode(
                x=alt.X('day:T', title='Date',
                        axis=alt.Axis(format="%b %d, %Y", labelAngle=-90, tickMinStep=1)),
                y=alt.Y('order_count:Q', title='Number of Abandoned Orders'),
                tooltip=['day:T', 'order_count:Q']
            )
            points = alt.Chart(abandoned_orders_per_day).mark_point(size=60, color='red').encode(
                x='day:T',
                y='order_count:Q',
                tooltip=['day:T', 'order_count:Q']
            )
            combined_chart = line_chart + points
            st.altair_chart(combined_chart, use_container_width=True)

        elif view == 'Abandoned Orders per Month':
            st.title('Abandoned Orders: Months')
            st.markdown("<h3 style='text-align: center;'>Abandoned Orders by Month</h3>", unsafe_allow_html=True)
            # Ensure 'month' is a datetime column
            abandoned_orders_per_month['month'] = pd.to_datetime(abandoned_orders_per_month['month'], format='%Y-%m-%d')
            # Create the chart with formatted month labels
            line_chart = alt.Chart(abandoned_orders_per_month).mark_line().encode(
                x=alt.X('month:T', title='Month', axis=alt.Axis(format='%b %Y', labelAngle=-45)),
                # Date type with custom formatting
                y=alt.Y('order_count:Q', title='Number of Abandoned Orders'),
                tooltip=[alt.Tooltip('month:T', title='Month'), 'order_count:Q']
            )
            points = alt.Chart(abandoned_orders_per_month).mark_point(size=60, color='red').encode(
                x=alt.X('month:T', title='Month'),
                y=alt.Y('order_count:Q', title='Number of Abandoned Orders'),
                tooltip=[alt.Tooltip('month:T', title='Month'), 'order_count:Q']
            )
            combined_chart = line_chart + points
            st.altair_chart(combined_chart, use_container_width=True)

        elif view == 'Abandoned Orders per Quarter':
            st.title('Abandoned Orders: Quarters')
            st.markdown("<h3 style='text-align: center;'>Abandoned Orders by Quarter</h3>", unsafe_allow_html=True)
            line_chart = alt.Chart(abandoned_orders_per_quarter).mark_line().encode(
                x=alt.X('quarter:N', title='Quarter'),
                y=alt.Y('order_count:Q', title='Number of Abandoned Orders'),
                tooltip=['quarter:N', 'order_count:Q']
            )
            points = alt.Chart(abandoned_orders_per_quarter).mark_point(size=60, color='red').encode(
                x='quarter:N',
                y='order_count:Q',
                tooltip=['quarter:N', 'order_count:Q']
            )
            combined_chart = line_chart + points
            st.altair_chart(combined_chart, use_container_width=True)
        elif view == 'Abandoned Orders per Year':
            st.title('Abandoned Orders: Years')
            st.markdown("<h3 style='text-align: center;'>Abandoned Orders by Year</h3>", unsafe_allow_html=True)
            line_chart = alt.Chart(abandoned_orders_per_year).mark_line().encode(
                x=alt.X('year:O', title='Year'),
                y=alt.Y('order_count:Q', title='Number of Abandoned Orders'),
                tooltip=['year:O', 'order_count:Q']
            )
            points = alt.Chart(abandoned_orders_per_year).mark_point(size=60, color='red').encode(
                x='year:O',
                y='order_count:Q',
                tooltip=['year:O', 'order_count:Q']
            )
            combined_chart = line_chart + points
            st.altair_chart(combined_chart, use_container_width=True)

        #Todo-Average abandoned orders per customer------------------------------------------------------------
        col1,col2 = st.columns(2)
        with col1:
            abandoned_orders_per_customer = df_abandoned_checkouts.groupby('Customer_ID')['Order_ID'].nunique()
            average_abandoned_orders = abandoned_orders_per_customer.mean()
            # Display the result using Streamlit
            st.markdown(
                f"""
                    <div class="card">
                        <p>Average abandoned orders per customer</p>
                        <h1>{int(average_abandoned_orders)}</h1>
                    </div>
                    """,
                unsafe_allow_html=True
            )
        with col2:
            most_abandoned_orders_per_customer = df_abandoned_checkouts.groupby('Customer_ID')['Order_ID'].nunique()
            most_abandoned_orders_per_customer = most_abandoned_orders_per_customer.max()
            # Display the result using Streamlit
            st.markdown(
                f"""
                    <div class="card">
                        <p>Most orders abandoned by a customer</p>
                        <h1>{int(most_abandoned_orders_per_customer)}</h1>
                    </div>
                    """,
                unsafe_allow_html=True
            )
        #Todo- Referring Sites by Abandoned Orders Top N
        df_abandoned_checkouts['Order_Referring_Site'] = df_abandoned_checkouts['Order_Referring_Site'].fillna('Unknown')  # Handle missing values
        df_abandoned_checkouts['Order_ID'] = df_abandoned_checkouts['Order_ID'].astype(str)  # Ensure Order_ID is treated as a string
        referring_sites = df_abandoned_checkouts.groupby('Order_Referring_Site')['Order_ID'].nunique().reset_index()
        referring_sites = referring_sites.rename(columns={'Order_ID': 'Total_Abandoned_Orders'})
        referring_sites = referring_sites.sort_values('Total_Abandoned_Orders', ascending=False)
        st.title("Total Abandoned Orders by Referring Sites")
        top_n = st.slider("Select Top N Referring Sites to Display", min_value=1, max_value=50, value=10,key="top_n_sites")
        top_referring_sites = referring_sites.head(top_n)
        st.markdown("<h3 style='text-align: center;'>Top N Referring Sites by Abandoned Orders</h3>",unsafe_allow_html=True)
        chart = alt.Chart(top_referring_sites).mark_bar().encode(
            x=alt.X('Order_Referring_Site:O', title='Referring Site', sort='-y'),  # X-axis for sites
            y=alt.Y('Total_Abandoned_Orders:Q', title='Total Abandoned Orders'),  # Y-axis for total abandoned orders
            color=alt.Color('Total_Abandoned_Orders:Q', legend=None),  # Color bars by count
            tooltip=['Order_Referring_Site:N', 'Total_Abandoned_Orders:Q']  # Add tooltips
        ).properties(width=700, height=400)
        chart_text = chart.mark_text(
            align='center',
            baseline='bottom',
            dy=-10,
            fontSize=12
        ).encode(
            text='Total_Abandoned_Orders:Q'
        )
        final_chart = chart + chart_text
        st.altair_chart(final_chart, use_container_width=True)

def show_products_page():
    st.title('Products Data')
    add_custom_css()
    #Todo-Average number of products ordered by a customer
    customer_product_counts = df_orders.groupby('Customer_ID')['Product_ID'].nunique().reset_index()
    average_products_per_customer = customer_product_counts['Product_ID'].mean()
    average_products_per_customer=round(average_products_per_customer,2)
    #Total Product counts---------------------------------------------
    df_products_cleaned = df_products.dropna(subset=['Product_Published_At'])
    total_product_count = df_products_cleaned['Product_ID'].nunique()
    col1,col2 = st.columns(2)
    with col1:
        st.markdown(
            f"""
                   <div class="card">
                       <p>Average number of products ordered by a customer</p>
                       <h1>{average_products_per_customer}</h1>
                   </div>
                   """,
            unsafe_allow_html=True
        )
    with col2:
        st.markdown(
            f"""
                   <div class="card">
                       <p>Total products</p>
                       <h1>{total_product_count}</h1>
                   </div>
                   """,
            unsafe_allow_html=True
        )
    st.title("Preview Filtered Product Data")
    filtered_products = filter_by_date(df_products, 'Product_Created_At')
    # with st.expander("Preview Filtered Products Data"):
    st.dataframe(filtered_products,use_container_width=True)

    #Todo-Count of products in each type----------------------------------------
    col1,col2=st.columns(2)
    with col1:
        df_products_ = df_products.dropna(subset=['Product_Published_At'])
        df_products_['Product_Type'] = df_products_['Product_Type'].replace("", "No Type")
        # Grouping by Product_Type and counting unique Product_ID
        product_counts = df_products_.groupby('Product_Type')['Product_ID'].nunique().reset_index()
        product_counts.columns = ['Product_Type', 'Count']
        # Streamlit layout
        st.title("Product Count by Type")
        st.markdown("### Visualizing the count of unique products in each type")
        # Slider for limiting top N product types
        top_n = st.slider("Select Top N Product Types to Display", min_value=1, max_value=len(product_counts), value=5)
        # Filtering for top N product types
        top_product_counts = product_counts.nlargest(top_n, 'Count')
        # Altair chart
        chart = alt.Chart(top_product_counts).mark_bar().encode(
            x=alt.X('Product_Type:O', title='Product Type', sort='-y'),
            y=alt.Y('Count:Q', title='Number of Products'),
            color=alt.Color('Count:Q', legend=None),
            tooltip=['Product_Type:N', 'Count:Q']
        ).properties(
            width=700,
            height=400,
            title="Top N Product Types by Count"
        )
        # Adding text labels on the bars
        text = chart.mark_text(
            align='center',
            baseline='middle',
            dy=-10  # Adjust text position
        ).encode(
            text='Count:Q'
        )
        # Combine chart and text
        final_chart = chart + text
        # Configure axis to set x-labels to 0-degree angle
        final_chart = final_chart.configure_axis(
            labelAngle=0,
            labelFontSize=12,
            titleFontSize=14
        )
        # Display chart
        st.altair_chart(final_chart, use_container_width=True)
    with col2:
        # Todo- Most Sold Product----------------------------------------------
        product_sales = df_orders.groupby('Product_Name')['Product_Quantity'].sum().reset_index()
        # Sort by total quantity sold in descending order
        product_sales = product_sales.sort_values(by='Product_Quantity', ascending=False)
        # Streamlit title and description
        st.title("Most Sold Products")
        st.markdown("### Displaying the most sold products by quantity")
        # Slider to display top N most sold products
        top_n = st.slider("Select Top N Most Sold Products to Display", min_value=1, max_value=len(product_sales),
                          value=5)
        # Get the top N most sold products
        top_sold_products = product_sales.head(top_n)
        # Altair chart for Most Sold Products
        chart = alt.Chart(top_sold_products).mark_bar().encode(
            x=alt.X('Product_Name:O', title='Product Name', sort='-y'),
            y=alt.Y('Product_Quantity:Q', title='Quantity Sold'),
            color=alt.Color('Product_Quantity:Q', legend=None),
            tooltip=['Product_Name:N', 'Product_Quantity:Q']
        ).properties(
            width=700,
            height=400,
            title="Top N Most Sold Products"
        )
        # Adding text labels on the bars
        text = chart.mark_text(
            align='center',
            baseline='middle',
            dy=-10  # Adjust text position
        ).encode(
            text='Product_Quantity:Q'
        )
        # Combine chart and text
        final_chart = chart + text
        final_chart = final_chart.configure_axis(
            labelAngle=0,
            labelFontSize=12,
            titleFontSize=14
        )
        # Display the final chart in Streamlit
        st.altair_chart(final_chart, use_container_width=True)

    #Todo-Most Price Product
    col1, col2 = st.columns(2)
    # Most Priced Products
    with col1:
        df_products_ = df_products.dropna(subset=['Product_Published_At'])
        most_priced = (
            df_products_.groupby(["Product_ID", "Product_Title"])
            .agg({"Variant_Price": "max"})
            .reset_index()
            .sort_values(by="Variant_Price", ascending=False)
        )
        # Streamlit layout for Most Priced Products
        st.title("Most Priced Products")
        st.markdown("### Displaying the most expensive products by price")
        # Slider to display top N most priced products
        top_n = st.slider("Select Top N Most Priced Products to Display", min_value=1, max_value=len(most_priced),value=5)
        top_priced_products = most_priced.head(top_n)
        # Altair chart for Most Priced Products
        chart = alt.Chart(top_priced_products).mark_bar().encode(
            x=alt.X('Product_Title:O', title='Product Title', sort='-y'),
            y=alt.Y('Variant_Price:Q', title='Price ($)'),
            color=alt.Color('Variant_Price:Q', legend=None),
            tooltip=['Product_Title:N', 'Variant_Price:Q']
        ).properties(
            width=700,
            height=400,
            title="Top N Most Priced Products"
        )
        # Adding text labels on the bars
        text = chart.mark_text(
            align='center',
            baseline='middle',
            dy=-10  # Adjust text position
        ).encode(
            text='Variant_Price:Q'
        )
        # Combine chart and text
        final_chart = chart + text
        final_chart = final_chart.configure_axis(
            labelAngle=0,
            labelFontSize=12,
            titleFontSize=14
        )
        st.altair_chart(final_chart, use_container_width=True)
    # Least Priced Products
    with col2:
        df_products_ = df_products.dropna(subset=['Product_Published_At'])
        # Least priced products
        Least_priced = (
            df_products_.groupby(["Product_ID", "Product_Title"])
            .agg({"Variant_Price": "min"})
            .reset_index()
        )
        # Correct sorting of Variant_Price
        price_order = Least_priced.sort_values(by="Variant_Price", ascending=True)["Product_Title"].tolist()
        # Streamlit layout
        st.title("Least Priced Products")
        st.markdown("### Displaying the Least expensive products by price")
        # Slider to display top N Least priced products
        top_n = st.slider("Select Top N Products to Display", min_value=1, max_value=len(Least_priced), value=5)
        top_priced_products = Least_priced.head(top_n)
        # Altair chart for visualization
        chart = alt.Chart(top_priced_products).mark_bar().encode(
            x=alt.X('Product_Title:O', title='Product Title', sort=price_order),  # Custom sort order for X axis
            y=alt.Y('Variant_Price:Q', title='Price ($)'),
            color=alt.Color('Variant_Price:Q', legend=None),
            tooltip=['Product_Title:N', 'Variant_Price:Q']
        ).properties(
            width=700,  # Same width for both charts
            height=400,  # Same height for both charts
            title="Top N Least Priced Products"
        )
        # Adding text labels on the bars
        text = chart.mark_text(
            align='center',
            baseline='middle',
            dy=-10  # Adjust text position
        ).encode(
            text='Variant_Price:Q'
        )
        # Combine chart and text
        final_chart = chart + text
        final_chart = final_chart.configure_axis(
            labelAngle=0,
            labelFontSize=12,
            titleFontSize=14
        )
        # Display chart
        st.altair_chart(final_chart, use_container_width=True)
    #Todo- List for unsold product----------------------------------
    df_products_cleaned = df_products.dropna(subset=['Product_Published_At'])
    sold_product_ids = df_orders['Product_ID'].unique()
    all_product_ids = df_products_cleaned['Product_ID']
    unsold_product_ids = all_product_ids[~all_product_ids.isin(sold_product_ids)]
    unsold_products = df_products_cleaned[df_products_cleaned['Product_ID'].isin(unsold_product_ids)]
    unsold_products_grouped = unsold_products.groupby(['Product_ID', 'Product_Title', 'Product_Published_At'],as_index=False).first()
    unsold_products_grouped['Product_ID'] = unsold_products_grouped['Product_ID'].astype(str).replace(",", "",regex=True)
    unsold_products_grouped['Product_Published_At'] = \
    unsold_products_grouped['Product_Published_At'].str.split("T").str[0]
    unsold_products_grouped['Product_Published_At'] = pd.to_datetime(unsold_products_grouped['Product_Published_At'])
    unsold_products_grouped_sorted = unsold_products_grouped.sort_values(by='Product_Published_At', ascending=True)
    unsold_products_grouped_sorted['Product_Published_At'] = unsold_products_grouped_sorted['Product_Published_At'].dt.date
    Data_display = unsold_products_grouped_sorted[['Product_ID', 'Product_Title', 'Product_Published_At']]
    # chart_col1,chart_col2 = st.columns(2)
    # with chart_col1:
    st.title("Unsold Products Summary")
    st.markdown("### List of Products That Have Not Been Sold")
    st.dataframe(Data_display,use_container_width=True)

    #Todo-Count of products in each price range
    df_products_cleaned = df_products.dropna(subset=['Product_Published_At'])
    # Find the minimum and maximum price in the dataset
    min_price = df_products_cleaned['Variant_Price'].min()
    max_price = df_products_cleaned['Variant_Price'].max()
    # Calculate the price range
    price_range = max_price - min_price
    # Calculate the IQR (Interquartile Range)
    q1 = df_products_cleaned['Variant_Price'].quantile(0.25)
    q3 = df_products_cleaned['Variant_Price'].quantile(0.75)
    iqr = q3 - q1
    # Number of data points
    n = len(df_products_cleaned)
    # Freedman-Diaconis Rule to calculate bin width
    if iqr > 0 and n > 1:
        bin_width = 2 * iqr / (n ** (1 / 3))  # Dynamic bin width
    else:
        bin_width = price_range / 5  # Fallback: divide into 5 bins if data is uniform
    # Calculate the number of bins dynamically
    num_bins = max(1, int(price_range / bin_width))  # Ensure at least 1 bin
    # Create dynamic price bins based on the min and max price
    price_bins = pd.cut(df_products_cleaned['Variant_Price'], bins=num_bins)
    # Adjust bin edges if any lower bounds are negative
    bin_edges = price_bins.cat.categories
    if bin_edges[0].left < 0:
        bin_edges = pd.IntervalIndex([pd.Interval(max(0, interval.left), interval.right) for interval in bin_edges])
        price_bins = pd.cut(df_products_cleaned['Variant_Price'], bins=bin_edges)
    # Create dynamic labels for the price bins
    price_labels = [f"{max(0, round(bin.left, 2))} - {round(bin.right, 2)}" for bin in price_bins.cat.categories]
    # Create a new column 'Price_Range' to categorize products into dynamic price ranges
    df_products_cleaned['Price_Range'] = pd.cut(df_products_cleaned['Variant_Price'], bins=num_bins,
                                                labels=price_labels, include_lowest=True)
    # Count the number of products in each price range
    price_range_counts = df_products_cleaned['Price_Range'].value_counts().reset_index()
    price_range_counts.columns = ['Price_Range', 'Count']
    # Streamlit layout
    st.title("Count of Products in Each Price Range")
    st.markdown("### Displaying the count of products in different price ranges")
    # Altair chart for Count of Products in Each Price Range
    chart = alt.Chart(price_range_counts).mark_bar().encode(
        x=alt.X('Price_Range:N', title='Price Range', sort=price_labels),
        y=alt.Y('Count:Q', title='Number of Products'),
        color=alt.Color('Count:Q', legend=None),
        tooltip=['Price_Range:N', 'Count:Q']
    ).properties(
        width=700,
        height=400,
        title="Count of Products in Each Price Range"
    )
    # Adding text labels on the bars
    text = chart.mark_text(
        align='center',
        baseline='middle',
        dy=-10  # Adjust text position
    ).encode(
        text='Count:Q'
    )
    # Combine chart and text
    final_chart = chart + text
    # Configure axis to set x-labels to 0-degree angle
    final_chart = final_chart.configure_axis(
        labelAngle=90,
        labelFontSize=10,
        titleFontSize=14
    )
    # Display chart
    st.altair_chart(final_chart, use_container_width=True)

def show_revenue_page():
    st.title('Revenue Data')
    add_custom_css()
    df_unique_orders = df_orders.drop_duplicates(subset='Order_ID', keep='first')
    Total_price = df_unique_orders['Order_Total_Price'].sum()
    Total_price=round(Total_price,2)
    Average_Revenue_=df_unique_orders['Order_Total_Price'].mean()
    Average_Revenue=round(Average_Revenue_,2)
    Total_amaount_refund=df_unique_orders['Order_Refund_Amount'].sum()

    col1, col2,col3= st.columns(3)
    with col1:
        st.markdown(
            f"""
                       <div class="card">
                           <p>Total revenue</p>
                           <h1>{Total_price}</h1>
                           
                       </div>
                       """,
            unsafe_allow_html=True
        )
    with col2:
        st.markdown(
            f"""
                       <div class="card">
                           <p>Average revenue by customer</p>
                           <h1>{Average_Revenue}</h1>

                       </div>
                       """,
            unsafe_allow_html=True
        )
    with col3:
        st.markdown(
            f"""
                       <div class="card">
                           <p>Total amound refund</p>
                           <h1>{Total_amaount_refund}</h1>

                       </div>
                       """,
            unsafe_allow_html=True
        )

    st.title("Preview Filtered Revenue Data")
    filtered_products = filter_by_date(df_orders, 'Order_Created_At')
    # with st.expander("Preview Filtered Revenue Data"):
    st.dataframe(filtered_products)

    #Todo-Total revenue placed: weekday vs weekend-----------------------
    df_unique_orders = df_orders.drop_duplicates(subset='Order_ID', keep='first')
    # Ensure the 'Order_Created_At' column is in datetime format
    df_unique_orders['Order_Created_At'] = pd.to_datetime(df_unique_orders['Order_Created_At'], errors='coerce', utc=True)
    # Add a new column for Weekday/Weekend
    df_unique_orders['Weekday_Weekend'] = df_unique_orders['Order_Created_At'].dt.dayofweek.apply(
        lambda x: 'Weekend' if x >= 5 else 'Weekday'
    )
    # Calculate total revenue for weekdays and weekends
    weekday_revenue = df_unique_orders[df_unique_orders['Weekday_Weekend'] == 'Weekday']['Order_Total_Price'].sum()
    weekend_revenue = df_unique_orders[df_unique_orders['Weekday_Weekend'] == 'Weekend']['Order_Total_Price'].sum()
    # Prepare data for the pie chart
    revenues = [weekday_revenue, weekend_revenue]
    labels = ['Weekday', 'Weekend']
    pie_data_revenue = pd.DataFrame({
        'Category': labels,
        'Revenue': revenues,
        'Percentage': [(rev / sum(revenues)) * 100 for rev in revenues]
    })
    pie_data_revenue['Label'] = pie_data_revenue['Percentage'].round(1).astype(str) + '%'
    # Add formatted revenue with € symbol for tooltips
    pie_data_revenue['Total_Revenue'] = '€' + pie_data_revenue['Revenue'].round(2).astype(str)
    # Create the pie chart using Altair
    pie_chart_revenue = alt.Chart(pie_data_revenue).mark_arc().encode(
        theta=alt.Theta(field="Revenue", type="quantitative"),
        color=alt.Color(field="Category", type="nominal"),
        tooltip=["Category", "Total_Revenue:N", "Percentage"]
    )
    # Display the results in Streamlit
    st.write(f"Weekday Revenue: €{weekday_revenue:.2f} ({(weekday_revenue / sum(revenues)) * 100:.2f}%)")
    st.write(f"Weekend Revenue: €{weekend_revenue:.2f} ({(weekend_revenue / sum(revenues)) * 100:.2f}%)")
    st.title('Total Revenue Placed: Weekday vs Weekend')
    st.markdown("<h3 style='text-align: center;'>Revenue by Weekday/Weekend</h3>", unsafe_allow_html=True)
    st.altair_chart(pie_chart_revenue, use_container_width=True)

    # Todo-Total revenue placed: days of week--------------------------
    # Ensure unique orders by dropping duplicates
    df_unique_orders = df_orders.drop_duplicates(subset='Order_ID', keep='first')
    # Ensure the 'Order_Created_At' column is in datetime format
    df_unique_orders['Order_Created_At'] = pd.to_datetime(df_unique_orders['Order_Created_At'], errors='coerce',
                                                          utc=True)
    # Add a new column for Days of the Week
    df_unique_orders['days_of_week'] = df_unique_orders['Order_Created_At'].dt.dayofweek.apply(
        lambda x: ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][x]
    )
    # Calculate total revenue for each day of the week
    revenue_per_day = df_unique_orders.groupby('days_of_week')['Order_Total_Price'].sum()
    # Reorder the days of the week
    revenue_per_day = revenue_per_day.reindex(
        ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'], fill_value=0
    )
    # Prepare data for pie chart
    pie_data_revenue = pd.DataFrame({
        'Day': revenue_per_day.index,
        'Revenue': revenue_per_day.values
    })
    # Add formatted revenue with € symbol for tooltips
    pie_data_revenue['Total_Revenue'] = '€' + pie_data_revenue['Revenue'].round(2).astype(str)
    # Create the pie chart
    pie_chart_revenue = alt.Chart(pie_data_revenue).mark_arc().encode(
        theta=alt.Theta(field="Revenue", type="quantitative"),
        color=alt.Color(field="Day", type="nominal",
                        sort=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']),
        tooltip=["Day:N", "Total_Revenue:N"]
    )
    # Display the results in Streamlit
    st.title('Total Revenue Placed: Days of the Week')
    st.markdown("<h3 style='text-align: center;'>Revenue by Day of the Week</h3>", unsafe_allow_html=True)
    st.altair_chart(pie_chart_revenue, use_container_width=True)

    #Todo---Total revenue placed: hours of day-------------------------------
    df_unique_orders = df_orders.drop_duplicates(subset='Order_ID', keep='first')
    # Ensure the 'Order_Created_At' column is in datetime format
    df_unique_orders['Order_Created_At'] = pd.to_datetime(df_unique_orders['Order_Created_At'], errors='coerce',utc=True)
    # Add a new column for Hour of the Day
    df_unique_orders['hour_of_day'] = df_unique_orders['Order_Created_At'].dt.hour + 1  # Shift hours to 1-24 range
    # Calculate total revenue for each hour of the day
    revenue_per_hour = df_unique_orders.groupby('hour_of_day')['Order_Total_Price'].sum()
    # Reindex to ensure all hours from 1 to 24 are included
    revenue_per_hour = revenue_per_hour.reindex(range(1, 25), fill_value=0)
    # Prepare data for the chart
    hour_revenue_data = pd.DataFrame({
        'Hour of Day': revenue_per_hour.index,
        'Total Revenue': revenue_per_hour.values
    })

    # Add formatted revenue with € symbol for tooltips
    hour_revenue_data['Overall Revenue'] = '€' + hour_revenue_data['Total Revenue'].round(2).astype(str)
    # Display the title and description
    st.title('Total Revenue Placed: Hours of Day')
    st.markdown("<h3 style='text-align: center;'>Revenue by Hour of the Day</h3>", unsafe_allow_html=True)
    # Create a line chart
    line_chart = alt.Chart(hour_revenue_data).mark_line().encode(
        x=alt.X('Hour of Day:O', title='Hour of Day', scale=alt.Scale(domain=list(range(1, 25)))),
        y=alt.Y('Total Revenue:Q', title='Total Revenue (€)'),
        tooltip=['Hour of Day', 'Overall Revenue']
    ).properties(
        width=700,
        height=400
    )
    # Add points to the line chart
    points = alt.Chart(hour_revenue_data).mark_point(size=100, color='blue').encode(
        x=alt.X('Hour of Day:O', title='Hour of Day'),
        y=alt.Y('Total Revenue:Q', title='Total Revenue (€)'),
        tooltip=['Hour of Day', 'Overall Revenue']
    )
    # Combine the line chart and points
    combined_chart = line_chart + points
    st.altair_chart(combined_chart, use_container_width=True)

    #Todo-Total revenue placed: day, month, quarter, year----------------------------
    df_unique_orders = df_orders.drop_duplicates(subset='Order_ID', keep='first')
    # Ensure the 'Order_Created_At' column is in datetime format
    df_unique_orders['Order_Created_At'] = pd.to_datetime(df_unique_orders['Order_Created_At'], errors='coerce',
                                                          utc=True)
    # Extract the day, month, quarter, and year
    df_unique_orders['day'] = df_unique_orders['Order_Created_At'].dt.date
    df_unique_orders['month'] = df_unique_orders['Order_Created_At'].dt.to_period('M').astype(str)  # Year-Month format
    df_unique_orders['quarter'] = df_unique_orders['Order_Created_At'].dt.to_period('Q').astype(
        str)  # Year-Quarter format
    df_unique_orders['year'] = df_unique_orders['Order_Created_At'].dt.year
    # Group by day, month, quarter, and year to calculate total revenue
    revenue_per_day = df_unique_orders.groupby('day')['Order_Total_Price'].sum().reset_index()
    revenue_per_month = df_unique_orders.groupby('month')['Order_Total_Price'].sum().reset_index()
    revenue_per_quarter = df_unique_orders.groupby('quarter')['Order_Total_Price'].sum().reset_index()
    revenue_per_year = df_unique_orders.groupby('year')['Order_Total_Price'].sum().reset_index()
    # Streamlit Visualization---
    st.title('Revenue Visualizations')
    view = st.radio("Select View", ['Revenue per Day', 'Revenue per Month', 'Revenue per Quarter', 'Revenue per Year'])
    if view == 'Revenue per Day':
        st.title('Revenue Placed: Days')
        st.markdown("<h3 style='text-align: center;'>Revenue by Day</h3>", unsafe_allow_html=True)
        # Define the line chart-------------
        line_chart = alt.Chart(revenue_per_day).mark_line().encode(
            x=alt.X(
                'day:T',
                title='Date',
                axis=alt.Axis(format="%b %d, %Y", labelAngle=-90, tickMinStep=1)  # Adjust axis labels
            ),
            y=alt.Y('Order_Total_Price:Q', title='Total Revenue (€)'),
            tooltip=['day:T', alt.Tooltip('Order_Total_Price:Q', format=",.2f", title="Total Revenue (€)")]
        )
        # Define the points for emphasis--------
        points = alt.Chart(revenue_per_day).mark_point(size=60, color='blue').encode(
            x='day:T',
            y='Order_Total_Price:Q',
            tooltip=['day:T', alt.Tooltip('Order_Total_Price:Q', format=",.2f", title="Total Revenue (€)")]
        )
        # Combine the line chart and points
        combined_chart = line_chart + points
        # Set chart properties
        combined_chart = combined_chart.properties(
            width=700,  # Adjust width for better readability
            height=400  # Adjust height
        )
        # Display the chart in Streamlit
        st.altair_chart(combined_chart, use_container_width=True)
    elif view == 'Revenue per Month':
        st.title('Revenue Placed: Months')
        st.markdown("<h3 style='text-align: center;'>Revenue by Month</h3>", unsafe_allow_html=True)
        revenue_per_month['month'] = pd.to_datetime(revenue_per_month['month'], format='%Y-%m')
        revenue_per_month['month'] = revenue_per_month['month'].dt.strftime('%b %Y')  # Convert to Month Year format
        line_chart = alt.Chart(revenue_per_month).mark_line().encode(
            x=alt.X('month:O', title='Month', axis=alt.Axis(labelAngle=-45)),
            y=alt.Y('Order_Total_Price:Q', title='Total Revenue (€)'),
            tooltip=['month:N', alt.Tooltip('Order_Total_Price:Q', format=",.2f", title="Total Revenue (€)")]
        )
        points = alt.Chart(revenue_per_month).mark_point(size=60, color='blue').encode(
            x='month:O',
            y='Order_Total_Price:Q',
            tooltip=['month:N', alt.Tooltip('Order_Total_Price:Q', format=",.2f", title="Total Revenue (€)")]
        )
        combined_chart = line_chart + points
        st.altair_chart(combined_chart, use_container_width=True)

    elif view == 'Revenue per Quarter':
        st.title('Revenue Placed: Quarters')
        st.markdown("<h3 style='text-align: center;'>Revenue by Quarter</h3>", unsafe_allow_html=True)
        line_chart = alt.Chart(revenue_per_quarter).mark_line().encode(
            x=alt.X('quarter:N', title='Quarter'),
            y=alt.Y('Order_Total_Price:Q', title='Total Revenue (€)'),
            tooltip=['quarter:N', alt.Tooltip('Order_Total_Price:Q', format=",.2f", title="Total Revenue (€)")]
        )
        points = alt.Chart(revenue_per_quarter).mark_point(size=60, color='blue').encode(
            x='quarter:N',
            y='Order_Total_Price:Q',
            tooltip=['quarter:N', alt.Tooltip('Order_Total_Price:Q', format=",.2f", title="Total Revenue (€)")]
        )
        combined_chart = line_chart + points
        st.altair_chart(combined_chart, use_container_width=True)

    elif view == 'Revenue per Year':
        st.title('Revenue Placed: Years')
        st.markdown("<h3 style='text-align: center;'>Revenue by Year</h3>", unsafe_allow_html=True)
        line_chart = alt.Chart(revenue_per_year).mark_line().encode(
            x=alt.X('year:O', title='Year'),
            y=alt.Y('Order_Total_Price:Q', title='Total Revenue (€)'),
            tooltip=['year:O', alt.Tooltip('Order_Total_Price:Q', format=",.2f", title="Total Revenue (€)")]
        )
        points = alt.Chart(revenue_per_year).mark_point(size=60, color='blue').encode(
            x='year:O',
            y='Order_Total_Price:Q',
            tooltip=['year:O', alt.Tooltip('Order_Total_Price:Q', format=",.2f", title="Total Revenue (€)")]
        )
        combined_chart = line_chart + points
        st.altair_chart(combined_chart, use_container_width=True)

    #Todo-Order Refering site chart
    df_unique_orders = df_orders.drop_duplicates(subset="Order_ID", keep="first")
    # Step 2: Calculate total revenue by referring sites
    total_revenue_by_site = df_unique_orders.groupby("Order_Referring_Site")["Order_Total_Price"].sum().reset_index()
    total_revenue_by_site.columns = ["Referring Site", "Total Revenue"]
    # Step 3: Streamlit layout
    st.title("Total Revenue by Referring Sites")
    st.markdown("### Visualizing the total revenue generated by different referring sites")
    # Slider for selecting top N referring sites
    top_n = st.slider("Select Top N Referring Sites to Display", min_value=1, max_value=len(total_revenue_by_site),value=5)
    # Filtering for top N referring sites
    top_revenue_sites = total_revenue_by_site.nlargest(top_n, "Total Revenue")
    # Step 4: Create Altair Chart
    chart = alt.Chart(top_revenue_sites).mark_bar().encode(
        x=alt.X("Referring Site:O", title="Referring Site", sort="-y"),
        y=alt.Y("Total Revenue:Q", title="Total Revenue (€)"),
        color=alt.Color("Total Revenue:Q", legend=None),
        tooltip=["Referring Site:N", alt.Tooltip("Total Revenue:Q", format=",.2f", title="Total Revenue (€)")],
    ).properties(
        width=700,
        height=400,
        title="Top N Referring Sites by Total Revenue"
    )
    # Adding text labels on the bars
    text = chart.mark_text(
        align="center",
        baseline="middle",
        dy=-10  # Adjust text position
    ).encode(
        text=alt.Text("Total Revenue:Q", format=",.2f")
    )
    # Combine chart and text
    final_chart = chart + text
    # Configure axis and chart aesthetics
    final_chart = final_chart.configure_axis(
        labelAngle=0,
        labelFontSize=12,
        titleFontSize=14
    )
    # Display the chart
    st.altair_chart(final_chart, use_container_width=True)

image_path = "D:\\Vinita\\Dyori_Image\\dyori_img.jpg"
image = Image.open(image_path)
image_resized = image.resize((300, 100))
st.sidebar.image(image_resized)

page = st.sidebar.selectbox("Select a Page", ['Customer Journey', 'Customer Data', 'Order Data', 'Abandoned Checkouts', 'Products','Revenue'])

if page == 'Customer Journey':
    show_cj_page()

elif page == 'Customer Data':
    show_customer_data_page()

elif page == 'Order Data':
    show_order_data_page()

elif page == 'Abandoned Checkouts':
    show_abandoned_checkouts_page()

elif page == 'Products':
    show_products_page()
elif page== 'Revenue':
    show_revenue_page()
