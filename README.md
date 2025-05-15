
# 💰 AI-Powered UPI Financial Analyzer

**An AI-powered Streamlit web app to analyze UPI transaction PDFs (PhonePe, Paytm) and provide personalized financial advice using Google Gemini LLM.**

---

## 🧾 Problem Statement

Develop an AI-powered application that processes UPI transaction statements from multiple apps (Paytm, GPay, PhonePe, etc.) and generates actionable insights and personalized financial advice using LLMs.

The system must:
- Extract transaction details from varied PDF formats
- Structure the data into a consistent format
- Analyze spending behavior
- Deliver tailored recommendations via an interactive dashboard or downloadable report


---

## 📌 Project Description

This project allows users to:
- Upload UPI transaction statements (PDFs) from **PhonePe** or **Paytm**
- Automatically **extract**, **structure**, and **analyze** transaction data
- Visualize **spending trends**, **top expenses**, and **wasteful transactions**
- Generate a **detailed financial report** powered by **Google Gemini LLM**
- Download the insights as a **PDF report**

---

## 🚀 Project Flow

1. **PDF Upload**
   - Users upload UPI transaction PDFs from Paytm/PhonePe.
   
2. **Source Detection & Parsing**
   - Auto-detects source and applies the respective parsing logic.

3. **Data Structuring**
   - Extracted data is converted into a structured DataFrame.
   - A CSV file is also saved (line #285: `self.df.to_csv("Extracted_data.csv")`).

4. **Visual Analysis**
   - Pie Chart: Credit vs Debit
   - Line Chart: Monthly trends
   - Bar Chart: Top expense categories
   - Table: Wasteful transactions (food, OTT, recharge, etc.)

5. **AI Report Generation**
   - Gemini generates a report based on the CSV (line #284: `st.dataframe(self.df)` is used for UI display).
   - Report includes spending behavior, savings tips, investment ideas, etc.

6. **Download**
   - Report is available in both **PDF** and **Text** formats.

---

## 🧪 Tech Stack

- Python
- Streamlit
- Google Gemini API (via `google.generativeai`)
- PyPDF2
- Pandas, Matplotlib, Seaborn
- ReportLab (for PDF report)

---

## 📦 Installation

Before running the project, install the required packages using `pip`:

```bash
pip install -r requirements.txt
```

Alternatively, install them manually:

```bash
pip install streamlit PyPDF2 pandas matplotlib seaborn google-generativeai reportlab markdown
```

---

## 🌐 How to Host on Streamlit Cloud

1. **Prepare the repo**
   - Add the following files:
     - `Financial_Analyzer.py`
     - `requirements.txt`
     - `.streamlit/config.toml` (optional for theming)

2. **requirements.txt**
   ```txt
   streamlit
   PyPDF2
   pandas
   matplotlib
   seaborn
   google-generativeai
   reportlab
   markdown
   ```

3. **Push to GitHub**

4. **Visit: [https://share.streamlit.io](https://share.streamlit.io)**
   - Connect your GitHub repo
   - Set main file as `Financial_Analyzer.py`

---

## 🛡 Free Software License

This project is released under a **free and open-source MIT License**.

---

## 📎 Author

Developed with ❤️ for personal financial literacy using AI.  
Date: 2025-05-15


---

## ⚙️ Optional Developer Notes

1. **Display All Transactions in the App:**
   - To show the extracted transaction table inside the Streamlit app, **uncomment line 284**:
     ```python
     st.dataframe(self.df)  # -> print all transaction
     ```

2. **Export Transactions as CSV File:**
   - To save all the structured transactions into a local CSV file, **uncomment line 285**:
     ```python
     self.df.to_csv("Extracted_data.csv", index=False)  # -> get Extracted data in csv file
     ```

These options can be useful for debugging or offline analysis.
