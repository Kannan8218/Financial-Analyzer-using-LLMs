import streamlit as st
import PyPDF2
import pandas as pd
import re
import tempfile
import os
import google.generativeai as genai
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
import markdown
class Financial_analysis:
    def __init__(self):
        self.API_key = "AIzaSyCWkg5nxN2v6DPhUCXyo7gcdED7btuM_Kg"
        self.uploaded_file,self.tmp_path,self.text,self.source,self.df = None,None,None,None,None
        self.spend_df,self.monthly,self.top_desc,self.waste_df = None,None,None,None
        self.prompt,self.csv_data,self.txt_bytes,self.pdf_bytes = None,None,None,None
    def extract_text_from_pdf(self):
        if self.tmp_path:
            try:
                text = ""
                with open(self.tmp_path, "rb") as f:
                    reader = PyPDF2.PdfReader(f)
                    for page in reader.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                return text
            except Exception as e:
                st.error(f"ERROR -> extract_text_from_pdf() Function (extracting PDF)\nError: {e}", icon="❌")
                return None
        else:
            st.warning(f"Warning: -> extract_text_from_pdf(): self.tmp_path is Empty", icon="⚠️")
            return None
    def detect_source(self):
        if "UPI Ref No" in self.text:
            return "Paytm"
        elif "Transaction ID" in self.text:
            return "PhonePe"
        return "Unknown"
    def parse_phonepe(self):
        lines = [line.strip() for line in self.text.splitlines() if line.strip()]
        lines = [l for l in lines if not l.startswith("Page") and "system generated" not in l.lower()]
        transactions = []
        i = 0
        date_pattern = re.compile(r"^[A-Za-z]{3} \d{1,2}, \d{4}$")
        time_pattern = re.compile(r"\d{1,2}:\d{2} [AP]M")
        amount_pattern = re.compile(r"INR\s+([\d,]+\.\d{2})")
        while i < len(lines):
            if date_pattern.match(lines[i]):
                block = [lines[i]]
                i += 1
                while i < len(lines) and not date_pattern.match(lines[i]):
                    block.append(lines[i])
                    i += 1
                try:
                    date = block[0]
                    time, txn_id, description, amount, txn_type = "", "", "", 0.0, ""
                    for line in block:
                        if not time:
                            t = time_pattern.search(line)
                            if t: time = t.group()
                        if "Transaction ID" in line:
                            txn_id = line.split(":")[-1].strip()
                        if "Debited from" in line: txn_type = "Debit"
                        if "Credited to" in line: txn_type = "Credit"
                        m = amount_pattern.search(line)
                        if m: amount = float(m.group(1).replace(",", ""))
                        if "Paid to" in line or "Received from" in line:
                            desc_line = line.replace(time, "").strip() if time in line else line.strip()
                            description = desc_line
                    transactions.append({"Date": date,"Time": time,"Description": description,"Transaction ID": txn_id,
                        "Amount": amount,"Type": txn_type})
                except:
                    continue
            else:
                i += 1
        return pd.DataFrame(transactions)
    def parse_paytm(self):
        lines = [line.strip() for line in self.text.splitlines() if line.strip()]
        transactions = []
        i = 0
        while i < len(lines):
            if re.match(r"\d{2} \w{3}", lines[i]) and i + 5 < len(lines):
                try:
                    date = lines[i]
                    raw = lines[i + 1]
                    match = re.match(r"(\d{1,2}:\d{2} [AP]M)(.*)", raw)
                    time = match.group(1).strip() if match else ""
                    description = match.group(2).strip() if match else raw.strip()
                    txn_id_match = re.search(r"UPI Ref No[:\s]+(\d+)", lines[i + 2])
                    txn_id = txn_id_match.group(1) if txn_id_match else ""
                    amount_line = lines[i + 5]
                    amt_match = re.search(r"([+-]?)\s*Rs\.?([\d,]+\.\d{2})", amount_line)
                    amount = float(amt_match.group(2).replace(",", "")) if amt_match else 0.0
                    sign = amt_match.group(1) if amt_match else ""
                    txn_type = "Credit" if sign == "+" or "Received" in description or "Refund" in description else "Debit"
                    transactions.append({"Date": date,"Time": time,"Description": description,"Transaction ID": txn_id,
                                         "Amount": amount,"Type": txn_type})
                    i += 6
                except:
                    i += 1
            else:
                i += 1
        return pd.DataFrame(transactions)
    def show_charts(self):
        st.markdown('<div class="title">📊 Financial Analysis Charts</div>', unsafe_allow_html=True)
        try:
            # Spending Pattern: Pic chart
            st.markdown('<div class="sub-title2">1. Spending Pattern(Credit vs Debit)</div>', unsafe_allow_html=True)
            self.spend_df = self.df.groupby("Type")["Amount"].sum().reset_index()
            fig1, ax1 = plt.subplots(figsize=(2,1))  # Small figure
            ax1.pie(self.spend_df["Amount"],labels=self.spend_df["Type"],autopct='%1.1f%%',startangle=90,radius=0.9,textprops={'fontsize': 4} ) # Reduce font size for labels and percentages
            st.pyplot(fig1)
        except Exception as e: 
            st.error("ERROR -> Main_fun() -> show_charts()(pie chart)\nError: {e}", icon="❌")
            return False
        try:
            # Monthly trend: Line chart
            st.markdown('<div class="sub-title2">2. Time-Based Trends</div>', unsafe_allow_html=True)
            self.df["Parsed_Date"] = pd.to_datetime(self.df["Date"], errors='coerce')
            self.monthly = self.df.groupby([self.df["Parsed_Date"].dt.to_period("M"), "Type"])["Amount"].sum().unstack(fill_value=0)
            self.monthly.index = self.monthly.index.astype(str)
            st.line_chart(self.monthly)
        except Exception as e: 
            st.error("ERROR -> Main_fun() -> show_charts()(Line chart)\nError: {e}", icon="❌")
            return False
        try:
            # Top descriptions: Bar chart
            st.markdown('<div class="sub-title2">3. Top Transaction Descriptions(Outflow)</div>', unsafe_allow_html=True)
            self.top_desc = self.df[self.df["Type"] == "Debit"].groupby("Description")["Amount"].sum().nlargest(10)
            fig2, ax2 = plt.subplots()
            sns.barplot(y=self.top_desc.index,x=self.top_desc.values,ax=ax2,hue=self.top_desc.index,palette="viridis",dodge=False,legend=False)
            ax2.set_xlabel("Amount")
            ax2.set_ylabel("Description")
            ax2.set_title("Top Debit Transactions")
            st.pyplot(fig2)
        except Exception as e: 
            st.error("ERROR -> Main_fun() -> show_charts()(Bar chart)\nError: {e}", icon="❌")
            return False
        try:
            # Wasteful transaction detection (example)
            st.markdown('<div class="sub-title2">4. ⚠️Potential Wasteful Transactions</div>', unsafe_allow_html=True)
            keywords = ["zomato", "swiggy", "recharge", "ott", "netflix", "hotstar"]
            mask = self.df["Description"].str.lower().apply(lambda x: any(k in x for k in keywords))
            self.waste_df = self.df[mask]
            st.dataframe(self.waste_df if not self.waste_df.empty else pd.DataFrame(columns=self.df.columns))
        except Exception as e: 
            st.error("ERROR -> Main_fun() -> show_charts()(Wasteful transaction)\nError: {e}", icon="❌")
            return False
        return True
    def generate_prompt(self):
        self.csv_data = self.df.to_csv(index=False)
        return f"""You are a certified financial analyst tasked with reviewing the following UPI transaction dataset and preparing a 
            detailed financial analysis report. Your report should be structured in a formal, business-professional tone and 
            include the following sections:
            1. **Executive Summary**: A concise overview of the individual's financial activity and key observations.
            2. **Income and Expenditure Overview**: A breakdown of total credited (income) and debited (expense) transactions, 
            along with a clear calculation of net cash flow.
            3. **Transaction Volume Summary**: Total number of credit and debit transactions, highlighting major inflow and outflow patterns.
            4. **Spending Behavior Analysis**: Identification of recurring payments, wasteful spending habits, or unusual financial activity.
            5. **Budget Optimization Recommendations**: Practical suggestions for improving financial habits, managing monthly budgets, and 
            minimizing non-essential expenses.
            6. **Savings and Investment Insights**: Recommendations for building a sustainable savings strategy and potential areas for future investment.
            7. **Conclusion and Strategic Advice**: Final observations with actionable financial planning tips for better money management and 
            long-term stability.
            Base your report solely on the provided transaction data. Present insights clearly and professionally, using bullet points and 
            financial terminology where appropriate. The Report should be in text format because user can download the report.
            Transaction Data:
            {self.csv_data}"""
    def generate_pdf(self, markdown_text: str) -> bytes:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter,rightMargin=40, leftMargin=40,topMargin=60, bottomMargin=60)
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='Justify', alignment=4)) 
        flowables = []
        html_text = markdown.markdown(markdown_text)
        for line in html_text.split("\n"):
            line = line.strip()
            if line:
                flowables.append(Paragraph(line, styles['Justify']))
                flowables.append(Spacer(1, 0.15 * inch))
        doc.build(flowables)
        buffer.seek(0)
        return buffer.read()
    def clear_data(self):
        try:
            if os.path.exists(self.tmp_path):
                os.remove(self.tmp_path)
        except Exception as e:
            st.warning(f"Warning: -> clear_data()(clean tmp_path)", icon="⚠️")
            return False
        try:
            del self.uploaded_file,self.text,self.source,self.df
            del self.spend_df,self.monthly,self.top_desc,self.waste_df
            del self.prompt,self.csv_data,self.txt_bytes,self.pdf_bytes
        except Exception as e:
            st.warning(f"Warning: -> clear_data()(clean all variable)", icon="⚠️")
            return False
        return True
    def Main_fun(self):
        try:
            # -------------------- Custom Styles --------------------
            st.markdown("""<style>
                .title {text-align: center;font-size: 34px;font-weight: bold;color: white;font-family: 'Lucida Calligraphy', cursive;
                        text-shadow: 2px 2px 5px rgba(76, 175, 80, 0.4);}
                .sub-title {text-align: center;font-size: 18px;color: #4CAF50;margin-bottom: 20px;font-family: 'Lucida Calligraphy', cursive;}
                .sub-title2 {text-align: left;font-size: 18px;color: white;margin-bottom: 20px;font-family: 'Georgia', cursive;}
                .report {background: rgba(0, 150, 136, 0.05);padding: 20px;border-radius: 10px;margin-top: 20px;border: 1px solid #B2DFDB;
                    font-size: 17px;line-height: 1.7;color: white;font-family: 'Comic Sans MS', cursive;}
                .banner {background: linear-gradient(to right, #2E7D32, #1B5E20);color: white;padding: 15px;font-size: 18px;border-radius: 8px;
                    text-align: center;font-weight: bold;margin-top: 20px;font-family: 'Calibri', sans-serif;}
                section[data-testid="stSidebar"] * {font-family: 'Georgia', serif;font-size: 16px;}
                button {background-color: #4CAF50;color: white;font-family: 'Georgia';
                font-size: 16px;border: none;padding: 10px 20px;border-radius: 8px;cursor: pointer;transition: background-color 0.3s ease;}
                button:hover {background-color: red;}
                </style>""", unsafe_allow_html=True)
            # -------------------- Sidebar --------------------
            st.sidebar.markdown("### 📂 Upload & Analyze")
            self.uploaded_file = st.sidebar.file_uploader("Upload PDF (Paytm or PhonePe)", type=["pdf"])
            st.sidebar.markdown("### ℹ️ How to Use This Tool?")
            st.sidebar.write("- Upload your Paytm or PhonePe UPI Transaction PDF.")
            st.sidebar.write("- AI will analyze your spending, savings, and generate a report.")
            st.sidebar.write("- Your personal data is not saved anywhere. If you want to download the generated report, click the download button below the report.")
            # -------------------- Title Section --------------------
            st.markdown('<h1 class="title">💰 AI-Powered Financial Insights</h1>', unsafe_allow_html=True)
            st.markdown('<p class="sub-title">Upload your UPI Statement PDF for an expert report</p>', unsafe_allow_html=True)
        except Exception as e:
                st.error(f"ERROR -> Main_fun() Function(Streamlit page setup)\nError: {e}", icon="❌")
                return False
        if self.uploaded_file:
            st.sidebar.success("File uploaded successfully!", icon="✅")
            try:
                with tempfile.NamedTemporaryFile(delete=False) as tmp:
                    tmp.write(self.uploaded_file.read())
                    self.tmp_path = tmp.name
            except Exception as e:
                st.error(f"ERROR -> Main_fun() Function(Read uploded file)\nError: {e}", icon="❌")
                return False
            with st.spinner("📄 Reading PDF..."):
                try:
                    self.text = self.extract_text_from_pdf()
                    if self.text is None:
                        st.warning(f"Warning: -> Main_fun() -> extract_text_from_pdf(): Error in extracted file data", icon="⚠️")
                        raise Exception
                except Exception as e:
                    st.error(f"ERROR -> Main_fun() Function(calling extract_text_from_pdf())\nError: {e}", icon="❌")
                    return False
                try:            
                    self.source = self.detect_source()
                    if self.source == "Unknown":
                        st.warning(f"Warning: -> Main_fun() -> detect_source(): Unknown file uploded", icon="⚠️")
                        return False
                except Exception as e:
                    st.error(f"ERROR -> Main_fun() Function(calling detect_source())\nError: {e}", icon="❌")
                    return False
                try:
                    if self.source == "Paytm":
                        self.df = self.parse_paytm()
                        if self.df.empty :
                            st.warning(f"Warning: -> Main_fun() -> parse_paytm(): self.df is empty", icon="⚠️")
                            return False
                    elif self.source == "PhonePe":
                        self.df = self.parse_phonepe()
                        if self.df.empty :
                            st.warning(f"Warning: -> Main_fun() -> parse_phonepe(): self.df is empty", icon="⚠️")
                            return False
                    else:
                        self.df = pd.DataFrame()
                        st.warning(f"Warning: -> Main_fun() self.df is empty", icon="⚠️")
                        return False
                except Exception as e:
                    st.error("ERROR -> Main_fun() -> parse paytm,PhonePe function\nError: {e}", icon="❌")
                    self.df = pd.DataFrame()
                    return False
            if self.df.empty:
                st.warning(f"Warning: -> extract_text_from_pdf(): self.df is Empty", icon="⚠️")
                return False
            else:
                #st.dataframe(self.df) # -> print all transaction
                #self.df.to_csv("Extracted_data.csv",index = False) -> get Extracted data in csv file
                if not self.show_charts():
                    st.error("ERROR -> Main_fun() -> (calling show_charts())\nError: {e}", icon="❌")
                    return False
                with st.spinner("Generating Report..."):
                    self.prompt = self.generate_prompt()
                    if (self.prompt is None) or (len(self.prompt)==0):
                        st.error("ERROR -> Main_fun() -> (calling show_charts())\nError: {e}", icon="❌")
                        return False
                    try:
                        genai.configure(api_key=self.API_key)
                        model = genai.GenerativeModel("models/gemini-2.0-flash")
                        response = model.generate_content(self.prompt)
                    except Exception as e:
                        st.error("ERROR -> Main_fun() -> (Gemini API Problem)\nError: {e}", icon="❌")
                        return False
                    st.markdown('<div class="title">📈 AI-Powered Financial Report</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="report">{response.text}</div>', unsafe_allow_html=True)
                    self.txt_bytes = response.text.encode("utf-8")
                    decoded_text = self.txt_bytes.decode("utf-8")  # decode bytes to string
                    self.pdf_bytes = self.generate_pdf(decoded_text)
                    st.download_button(label="Download_Report",
                        data=self.pdf_bytes,  # PDF content in bytes
                        file_name="financial_report.pdf",
                        mime="application/pdf",
                        on_click="ignore",
                        icon=":material/download:")
                    if not self.clear_data():
                        st.warning(f"Warning: -> Main_fun()(calling clear_data())", icon="⚠️")
                        return False 
        return True
if __name__ == '__main__':
    try:
        obj = Financial_analysis()
    except Exception as e:
        st.error("ERROR -> if __name__ == '__main__'(Class Object)\nError: {e}", icon="❌")
        exit()
    if not obj.Main_fun():
        st.stop()
        exit()        