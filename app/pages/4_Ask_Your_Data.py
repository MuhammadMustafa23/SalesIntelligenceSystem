import streamlit as st
import pandas as pd
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.db import get_engine
from utils.ai import get_gemini_client, SCHEMA_CONTEXT, FORBIDDEN_WORDS

st.set_page_config(page_title="Ask Your Data", page_icon="💬", layout="wide")
st.title("Ask your data")
st.caption("Type a question in plain English. Gemini writes the SQL, runs it against SQL Server, and answers in plain English.")

# Example questions for quick testing
st.markdown("**Try asking:**")
example_cols = st.columns(3)
examples = [
    "Which category had the highest cancellation rate in 2017?",
    "Who are the top 5 customers by total spend?",
    "What was the total revenue in 2018?"
]
clicked_example = None
for col, ex in zip(example_cols, examples):
    if col.button(ex, use_container_width=True):
        clicked_example = ex

st.divider()

question = st.text_input(
    "Your question",
    value=clicked_example if clicked_example else "",
    placeholder="e.g. Which payment method has the most cancelled orders?"
)

ask_clicked = st.button("Ask", type="primary")

if (ask_clicked or clicked_example) and question:
    client = get_gemini_client()
    engine = get_engine()

    with st.spinner("Writing SQL query..."):
        prompt = f"{SCHEMA_CONTEXT}\n\nUser question: {question}\n\nSQL query:"
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        sql_query = response.text.strip().replace('```sql', '').replace('```', '').strip()

    st.subheader("Generated SQL")
    st.code(sql_query, language="sql")

    if any(word in sql_query.upper() for word in FORBIDDEN_WORDS):
        st.error("This query contains a forbidden operation and was not executed.")
    else:
        with st.spinner("Running query..."):
            try:
                result_df = pd.read_sql(sql_query, engine)
            except Exception as e:
                st.error(f"Error executing query: {e}")
                result_df = None

        if result_df is not None:
            st.subheader("Result")
            st.dataframe(result_df, use_container_width=True)

            with st.spinner("Generating answer..."):
                explain_prompt = f"""
                The user asked: {question}
                The SQL query returned this data:
                {result_df.to_string(index=False)}

                Write a short, clear, 2-3 sentence answer in plain English based on this data.
                Do not mention SQL or databases. Just answer like a data analyst would.
                """
                final_answer = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=explain_prompt
                )

            st.subheader("Answer")
            st.success(final_answer.text)