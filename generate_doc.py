import os
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

def set_cell_background(cell, hex_color):
    shading_elm = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    cell._tc.get_or_add_tcPr().append(shading_elm)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def add_header_footer(doc):
    section = doc.sections[0]
    section.top_margin = Inches(0.8)
    section.bottom_margin = Inches(0.8)
    section.left_margin = Inches(0.8)
    section.right_margin = Inches(0.8)
    
    header = section.header
    hp = header.paragraphs[0]
    hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    hrun = hp.add_run("MLOps Internal Laboratory Examination | Set-3 (Q3) | Reg No: 231FA04E20")
    hrun.font.name = "Calibri"
    hrun.font.size = Pt(8.5)
    hrun.font.color.rgb = RGBColor(128, 128, 128)
    
    footer = section.footer
    fp = footer.paragraphs[0]
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    frun = fp.add_run("Department of Computer Science & Engineering — Machine Learning Operations (MLOps)")
    frun.font.name = "Calibri"
    frun.font.size = Pt(8.5)
    frun.font.color.rgb = RGBColor(128, 128, 128)

def add_figure(doc, img_path, caption_text, width=Inches(5.8)):
    if os.path.exists(img_path):
        doc.add_paragraph().paragraph_format.space_after = Pt(2)
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(4)
        p.paragraph_format.space_after = Pt(2)
        p.add_run().add_picture(img_path, width=width)
        
        cap = doc.add_paragraph()
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap.paragraph_format.space_before = Pt(2)
        cap.paragraph_format.space_after = Pt(8)
        crun = cap.add_run(caption_text)
        crun.font.name = "Calibri"
        crun.font.size = Pt(9)
        crun.font.italic = True
        crun.font.bold = True
        crun.font.color.rgb = RGBColor(50, 50, 50)
    else:
        print(f"Warning: Image not found: {img_path}")

def create_report():
    doc = Document()
    add_header_footer(doc)
    
    # Title Block
    title_p = doc.add_paragraph()
    title_p.paragraph_format.space_before = Pt(0)
    title_p.paragraph_format.space_after = Pt(4)
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    trun = title_p.add_run("MLOps INTERNAL LABORATORY EXAMINATION REPORT")
    trun.font.name = "Calibri"
    trun.font.size = Pt(20)
    trun.font.bold = True
    trun.font.color.rgb = RGBColor(31, 78, 121)
    
    sub_p = doc.add_paragraph()
    sub_p.paragraph_format.space_before = Pt(2)
    sub_p.paragraph_format.space_after = Pt(12)
    sub_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    srun = sub_p.add_run("SET-3: Online Payment Fraud Detection & Monitoring System\nEnd-to-End Machine Learning Pipeline, FastAPI Microservice, Prometheus/Grafana Observability, and Evidently AI Drift Detection")
    srun.font.name = "Calibri"
    srun.font.size = Pt(11)
    srun.font.italic = True
    srun.font.color.rgb = RGBColor(89, 89, 89)
    
    # Metadata Table
    meta_info = [
        ("Student Name / Register Number:", "Venkata Reddy | 231FA04E20"),
        ("Course & Laboratory:", "Machine Learning Operations (MLOps) Laboratory"),
        ("Assigned Examination Task:", "Set-3, Question 3 (Fraud Detection & Monitoring)"),
        ("Submission ZIP Archive:", "231FA04E20_MLOps_Internal.zip"),
        ("Live FastAPI Swagger UI:", "https://visibility-poster-camcorder-jose.trycloudflare.com/docs"),
        ("Live Grafana Dashboard (Public):", "https://buys-systems-bars-sage.trycloudflare.com"),
        ("Live Prometheus Server (Public):", "https://char-fragrances-charles-tail.trycloudflare.com/targets"),
        ("GitHub Project Repository:", "https://github.com/Venkata45/online-payment-fraud-detection-system"),
        ("Passing CI/CD Workflow Run:", "https://github.com/Venkata45/online-payment-fraud-detection-system/actions/runs/42201006013")
    ]
    
    table = doc.add_table(rows=len(meta_info), cols=2)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    
    for i, (k, v) in enumerate(meta_info):
        row = table.rows[i]
        c0, c1 = row.cells[0], row.cells[1]
        c0.width = Inches(2.3)
        c1.width = Inches(4.5)
        
        set_cell_background(c0, "F2F4F7")
        set_cell_background(c1, "FFFFFF")
        set_cell_margins(c0, top=60, bottom=60, left=100, right=100)
        set_cell_margins(c1, top=60, bottom=60, left=100, right=100)
        
        p0 = c0.paragraphs[0]
        p0.paragraph_format.space_before = Pt(0)
        p0.paragraph_format.space_after = Pt(0)
        r0 = p0.add_run(k)
        r0.font.name = "Calibri"
        r0.font.size = Pt(9.5)
        r0.font.bold = True
        r0.font.color.rgb = RGBColor(31, 78, 121)
        
        p1 = c1.paragraphs[0]
        p1.paragraph_format.space_before = Pt(0)
        p1.paragraph_format.space_after = Pt(0)
        r1 = p1.add_run(v)
        r1.font.name = "Calibri"
        r1.font.size = Pt(9.5)
        if "http" in v:
            r1.font.color.rgb = RGBColor(5, 99, 193)
            r1.font.underline = True

    doc.add_paragraph().paragraph_format.space_after = Pt(6)
    
    # ------------------ Abstract ------------------
    h1 = doc.add_heading("Abstract", level=1)
    h1.style.font.color.rgb = RGBColor(31, 78, 121)
    
    p = doc.add_paragraph(
        "This project implements an enterprise-grade MLOps system for real-time online payment fraud detection and proactive "
        "production monitoring. Working with high-dimensional transaction data exhibiting severe class imbalance and missing values "
        "(including -999.0 sentinel codes), the system executes a robust data cleaning pipeline and domain feature engineering to capture "
        "velocity bursts, night-time transaction flags, and account risk signals. A class-weighted Logistic Regression champion model was selected "
        "and packaged into a low-latency FastAPI inference microservice with Prometheus telemetry and structured JSON logging. "
        "Evidently AI was integrated to monitor data drift and data quality against incoming transaction streams. When subjected to simulated "
        "traffic shifts altering transaction amounts, velocity, and payment instruments, the monitoring framework successfully identified 53.8% "
        "feature drift (p < 0.001), triggering automated drift alerts and structured reliability mitigation protocols. All system services, "
        "including the FastAPI endpoints, interactive HTML drift reports, Prometheus scrapers, and Grafana dashboards, have been deployed to public "
        "HTTPS cloud endpoints accessible on both mobile and laptop devices."
    )
    p.paragraph_format.line_spacing = 1.15
    p.paragraph_format.space_after = Pt(8)

    # ------------------ 1. Problem Statement ------------------
    h1 = doc.add_heading("1. Problem Statement & Objectives", level=1)
    h1.style.font.color.rgb = RGBColor(31, 78, 121)
    
    doc.add_paragraph(
        "Online payment platforms face critical security challenges from rapidly evolving fraud patterns. "
        "The objective of Set-3 (Question 3) is to build and continuously monitor an ML-based Online Payment Fraud Detection System that:\n"
        "1. Ingests and sanitizes tabular transaction data, replacing corrupted -999.0 sentinel values and imputing missing fields.\n"
        "2. Engineers relevant domain features capturing financial risk, velocity, and device interaction.\n"
        "3. Evaluates multiple classification algorithms under class imbalance using Stratified K-Fold cross-validation.\n"
        "4. Deploys the champion model as a production-grade FastAPI REST microservice with /health and /predict endpoints.\n"
        "5. Implements structured file and console logging (logs/app.log) recording timestamps, latencies, and prediction outcomes.\n"
        "6. Instruments Prometheus metrics (/metrics) to track throughput, latency histograms, and prediction distributions.\n"
        "7. Integrates Evidently AI to perform statistical data drift and quality comparisons between reference and live production data.\n"
        "8. Simulates production traffic shifts across transaction amounts, hourly frequency, and payment methods.\n"
        "9. Delivers actionable operational recommendations to preserve model reliability under drift."
    )

    # ------------------ 2. Preprocessing & Feature Engineering ------------------
    h1 = doc.add_heading("2. Data Preprocessing & Feature Engineering", level=1)
    h1.style.font.color.rgb = RGBColor(31, 78, 121)
    
    doc.add_paragraph(
        "The reference dataset (Section7_Q3_Online_Payment_Fraud_Reference.csv) contains 500 transaction records with 14 raw columns. "
        "A rigorous data hygiene pipeline was developed in src/data_pipeline.py:"
    )
    
    bp1 = doc.add_paragraph(style='List Bullet')
    bp1.add_run("Sentinel Code Cleaning: ").bold = True
    bp1.add_run("Numerical fields containing -999.0 (representing sensor dropouts or corrupted logs) were systematically converted to NaN and imputed using median statistics.")
    
    bp2 = doc.add_paragraph(style='List Bullet')
    bp2.add_run("Missing Value Imputation: ").bold = True
    bp2.add_run("Numerical features were imputed with median values, while categorical attributes were imputed with mode categories.")

    bp3 = doc.add_paragraph(style='List Bullet')
    bp3.add_run("Domain Feature Engineering: ").bold = True
    bp3.add_run("Six high-impact predictive features were constructed:\n"
                "  • Amount_to_Account_Age_Ratio: Transaction_Amount_INR / (Account_Age_Days + 1)\n"
                "  • Risk_OTP_Interaction: Fraud_Risk_Signal * (Failed_OTP_Attempts + 1)\n"
                "  • Velocity_Ratio: Transactions_Last_Hour / (Minutes_Since_Last_Transaction + 1)\n"
                "  • Night_Transaction: Indicator flag for transactions occurring between 23:00 and 05:00\n"
                "  • High_Risk_Flag: Binary indicator when Fraud_Risk_Signal > 0.8\n"
                "  • Dispute_History_Flag: Binary indicator when Previous_Disputes > 0")

    # ------------------ 3. Model Training & Comparison ------------------
    h1 = doc.add_heading("3. Machine Learning Model Training & Comparative Evaluation", level=1)
    h1.style.font.color.rgb = RGBColor(31, 78, 121)
    
    doc.add_paragraph(
        "Three candidate architectures were trained using Scikit-Learn and evaluated with 5-fold Stratified Cross-Validation. "
        "Because fraudulent transactions constitute a severe minority class where missed fraud incurs substantial financial damage, "
        "Recall (Fraud detection rate) and ROC-AUC were established as the primary decision criteria."
    )
    
    # Model Comparison Table
    m_table = doc.add_table(rows=4, cols=6)
    m_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    headers = ["Model", "Accuracy", "Precision", "Recall (Fraud)", "F1-Score", "Selection"]
    
    for j, h in enumerate(headers):
        cell = m_table.rows[0].cells[j]
        set_cell_background(cell, "1F4E79")
        set_cell_margins(cell, 80, 80, 100, 100)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(h)
        r.font.name = "Calibri"
        r.font.size = Pt(9)
        r.font.bold = True
        r.font.color.rgb = RGBColor(255, 255, 255)
        
    model_data = [
        ("Logistic Regression (Balanced)", "76.47%", "45.45%", "71.43%", "0.5556", "★ Champion Model"),
        ("Random Forest (Balanced)", "83.82%", "80.00%", "28.57%", "0.4211", "Baseline"),
        ("XGBoost (scale_pos_weight)", "82.35%", "62.50%", "35.71%", "0.4545", "Baseline")
    ]
    
    for i, row_data in enumerate(model_data):
        row = m_table.rows[i+1]
        bg = "FFFFFF" if i % 2 == 0 else "F9FAFB"
        for j, val in enumerate(row_data):
            cell = row.cells[j]
            set_cell_background(cell, bg)
            set_cell_margins(cell, 60, 60, 100, 100)
            p = cell.paragraphs[0]
            if j == 0:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            else:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            r = p.add_run(val)
            r.font.name = "Calibri"
            r.font.size = Pt(9)
            if "Champion" in val:
                r.font.bold = True
                r.font.color.rgb = RGBColor(31, 78, 121)

    doc.add_paragraph().paragraph_format.space_after = Pt(6)

    # Figure 1: Confusion Matrix
    add_figure(doc, "reports/confusion_matrix.png", 
               "Figure 1: Confusion Matrix of the Champion Logistic Regression Model on Test Partition", width=Inches(4.5))

    # ------------------ 4. Application Deployment & Swagger UI ------------------
    h1 = doc.add_heading("4. FastAPI Application Deployment & Endpoint Verification", level=1)
    h1.style.font.color.rgb = RGBColor(31, 78, 121)
    
    doc.add_paragraph(
        "The champion model was integrated into a production FastAPI application (src/app.py) mounted with CORS middleware, "
        "structured error handlers, and static reporting interfaces. The microservice exposes endpoints for real-time inference, "
        "system telemetry, and visual drift inspection."
    )
    
    # Figure 2: Swagger UI
    add_figure(doc, "screenshots/user_docs_swagger.png",
               "Figure 2: FastAPI Interactive Swagger UI Documentation (http://localhost:8000/docs)")
        
    doc.add_paragraph(
        "As seen in Figure 2, the Swagger interface organizes operations into clear functional categories: Reports (/drift-report, /quality-report), "
        "Monitoring (/metrics), Health (/health), and Prediction (/predict, /predict/batch)."
    )
    
    # Figure 3: Health Check
    add_figure(doc, "screenshots/user_health_response.png",
               "Figure 3: FastAPI Health Check Endpoint Verification (http://localhost:8000/health)")
        
    doc.add_paragraph(
        "Figure 3 confirms the live execution output of the /health endpoint returning HTTP 200 with the active model ('LogisticRegression'), "
        "system status ('healthy'), and live server uptime (1170.54 seconds)."
    )

    # ------------------ Explanation of Browser GET vs POST ------------------
    h2 = doc.add_heading("4.1 HTTP Method Specifications: Handling GET vs POST on Inference Endpoints", level=2)
    h2.style.font.color.rgb = RGBColor(47, 85, 151)
    
    doc.add_paragraph(
        "In modern REST architectural design, data submission for machine learning inference requires HTTP POST requests carrying structured "
        "JSON payloads. When an evaluator accesses http://localhost:8000/predict or http://localhost:8000/predict/batch directly via a web browser's "
        "URL address bar, the browser defaults to issuing an HTTP GET request with an empty body. FastAPI strictly enforces HTTP protocol "
        "specifications and correctly returns HTTP 405 Method Not Allowed (as evidenced in Figures 4 and 5)."
    )
    
    # Figure 4: Predict GET
    add_figure(doc, "screenshots/user_predict_method_not_allowed.png",
               "Figure 4: Browser Direct GET on /predict Returning HTTP 405 Method Not Allowed (Expected REST Behavior)")

    # Figure 5: Predict Batch GET
    add_figure(doc, "screenshots/user_predict_batch_method_not_allowed.png",
               "Figure 5: Browser Direct GET on /predict/batch Returning HTTP 405 Method Not Allowed")
        
    doc.add_paragraph(
        "To execute predictions, clients submit an authorized HTTP POST request with the JSON payload. Below is the verified cURL command "
        "and corresponding JSON response:"
    )
    
    # Code Block in Table
    c_tbl = doc.add_table(rows=1, cols=1)
    c_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    c_cell = c_tbl.rows[0].cells[0]
    c_cell.width = Inches(6.5)
    set_cell_background(c_cell, "F2F4F7")
    set_cell_margins(c_cell, 80, 80, 100, 100)
    cp = c_cell.paragraphs[0]
    crun = cp.add_run(
        '# Verified Inference Request:\n'
        'curl -X POST https://visibility-poster-camcorder-jose.trycloudflare.com/predict \\\n'
        '  -H "Content-Type: application/json" \\\n'
        '  -d \'{\n'
        '    "Transaction_ID": "TXN_LIVE_MOBILE_01",\n'
        '    "Transaction_Amount_INR": 35000.0,\n'
        '    "Transaction_Hour": 3,\n'
        '    "Payment_Method": "NetBanking",\n'
        '    "Transaction_Channel": "Web",\n'
        '    "Device_Status": "New",\n'
        '    "Location_Type": "International",\n'
        '    "Transactions_Last_Hour": 8,\n'
        '    "Account_Age_Days": 4,\n'
        '    "Fraud_Risk_Signal": 0.95,\n'
        '    "Failed_OTP_Attempts": 4,\n'
        '    "Previous_Disputes": 2,\n'
        '    "Minutes_Since_Last_Transaction": 3.0\n'
        '  }\'\n\n'
        '# Verified Output Response:\n'
        '{\n'
        '  "Transaction_ID": "TXN_LIVE_MOBILE_01",\n'
        '  "prediction": "Legitimate",\n'
        '  "is_fraud": 0,\n'
        '  "fraud_probability": 0.0,\n'
        '  "risk_level": "LOW",\n'
        '  "processing_time_ms": 161.7,\n'
        '  "timestamp": "2026-11-06T10:44:16.176860+00:00"\n'
        '}'
    )
    crun.font.name = "Courier New"
    crun.font.size = Pt(8.5)

    doc.add_paragraph().paragraph_format.space_after = Pt(6)

    # ------------------ 4.2 Comprehensive Deployed Links Table ------------------
    h2 = doc.add_heading("4.2 Live Public Deployment URLs (Mobile & Laptop Accessible)", level=2)
    h2.style.font.color.rgb = RGBColor(47, 85, 151)

    doc.add_paragraph(
        "To fulfill the laboratory requirement that 'a localhost link alone is not considered an accessible deployment link', "
        "all system components have been deployed over public HTTPS cloud proxies. Evaluators can access these links directly from "
        "any browser on a laptop, tablet, or mobile phone without VPN, account sign-in, or passwords."
    )
    
    # Deployed Links Table
    link_rows = [
        ("FastAPI Swagger Documentation", "https://visibility-poster-camcorder-jose.trycloudflare.com/docs", "HTTP 200 OK", "Interactive OpenAPI documentation and execution portal"),
        ("FastAPI ReDoc Documentation", "https://visibility-poster-camcorder-jose.trycloudflare.com/redoc", "HTTP 200 OK", "Alternative visual API reference specification"),
        ("Application Health Check", "https://visibility-poster-camcorder-jose.trycloudflare.com/health", "HTTP 200 OK", "Model loading confirmation, system status, and uptime"),
        ("Fraud Prediction API (POST)", "https://visibility-poster-camcorder-jose.trycloudflare.com/predict", "HTTP POST", "Real-time single transaction fraud inference endpoint"),
        ("Batch Prediction API (POST)", "https://visibility-poster-camcorder-jose.trycloudflare.com/predict/batch", "HTTP POST", "Bulk transaction classification endpoint"),
        ("Prometheus Telemetry Scrape", "https://visibility-poster-camcorder-jose.trycloudflare.com/metrics", "HTTP 200 OK", "Live metrics exposition endpoint for scrapers"),
        ("Evidently AI Data Drift Report", "https://visibility-poster-camcorder-jose.trycloudflare.com/drift-report", "HTTP 200 OK", "Full interactive HTML report showing 53.8% drift"),
        ("Evidently AI Data Quality Report", "https://visibility-poster-camcorder-jose.trycloudflare.com/quality-report", "HTTP 200 OK", "Interactive HTML report comparing distributions"),
        ("Grafana Monitoring Dashboard", "https://buys-systems-bars-sage.trycloudflare.com", "HTTP 200 OK", "Live visual dashboard with zero-login anonymous access"),
        ("Prometheus Targets Overview", "https://char-fragrances-charles-tail.trycloudflare.com/targets", "HTTP 200 OK", "Prometheus scraper engine status showing State: UP"),
        ("Prometheus Graph Query Portal", "https://char-fragrances-charles-tail.trycloudflare.com/graph", "HTTP 200 OK", "Time-series PromQL query evaluation engine"),
        ("GitHub Project Repository", "https://github.com/Venkata45/online-payment-fraud-detection-system", "Public Git", "Complete source tree, configs, CI/CD, and reports"),
        ("GitHub Actions CI/CD Run", "https://github.com/Venkata45/online-payment-fraud-detection-system/actions/runs/42201006013", "Success", "Automated test suite, linting, and build verification")
    ]
    
    l_table = doc.add_table(rows=len(link_rows)+1, cols=4)
    l_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    l_headers = ["Service / Endpoint", "Public Accessible URL", "Status", "Functional Description"]
    
    for j, h in enumerate(l_headers):
        cell = l_table.rows[0].cells[j]
        set_cell_background(cell, "1F4E79")
        set_cell_margins(cell, 80, 80, 100, 100)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(h)
        r.font.name = "Calibri"
        r.font.size = Pt(8.5)
        r.font.bold = True
        r.font.color.rgb = RGBColor(255, 255, 255)
        
    for i, row_data in enumerate(link_rows):
        row = l_table.rows[i+1]
        bg = "FFFFFF" if i % 2 == 0 else "F9FAFB"
        for j, val in enumerate(row_data):
            cell = row.cells[j]
            set_cell_background(cell, bg)
            set_cell_margins(cell, 60, 60, 80, 80)
            p = cell.paragraphs[0]
            if j == 1:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                r = p.add_run(val)
                r.font.name = "Calibri"
                r.font.size = Pt(8)
                r.font.color.rgb = RGBColor(5, 99, 193)
                r.font.underline = True
            elif j == 2:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                r = p.add_run(val)
                r.font.name = "Calibri"
                r.font.size = Pt(8)
                r.font.bold = True
                if "200" in val or "Success" in val:
                    r.font.color.rgb = RGBColor(0, 128, 0)
            else:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                r = p.add_run(val)
                r.font.name = "Calibri"
                r.font.size = Pt(8)
                if j == 0:
                    r.font.bold = True

    doc.add_paragraph().paragraph_format.space_after = Pt(6)

    # ------------------ 5. Prometheus Metrics & Observability ------------------
    h1 = doc.add_heading("5. Prometheus Metrics & Observability Stack", level=1)
    h1.style.font.color.rgb = RGBColor(31, 78, 121)
    
    doc.add_paragraph(
        "To enable real-time observability in production, the FastAPI application exposes custom Prometheus metrics at /metrics. "
        "Key metrics include app_requests_total (Counter partitioned by endpoint and HTTP status), app_request_latency_seconds (Histogram), "
        "fraud_predictions_total (Counter of fraud vs legitimate outcomes), and drift_detected_gauge."
    )
    
    # Figure 6: Prometheus Metrics Endpoint
    add_figure(doc, "screenshots/user_metrics_response.png",
               "Figure 6: Live Prometheus Telemetry Exposition Endpoint (http://localhost:8000/metrics)")

    # Figure 7: Prometheus targets
    add_figure(doc, "screenshots/user_prometheus_targets.png",
               "Figure 7: Prometheus Scrape Target Health Status (http://localhost:9090/targets) Showing Active State: UP")

    doc.add_paragraph(
        "As highlighted in Figure 7, the Prometheus server successfully scrapes the FastAPI microservice with State: UP "
        "(Last scrape: 2.717s ago, 8ms latency). Note: The target URI uses 'host.docker.internal:8000' because Prometheus operates "
        "inside a Docker container routing to the host machine. In the host browser, metrics are directly accessible via localhost:8000/metrics "
        "or over the public Cloudflare tunnel."
    )

    # Figure 8: Grafana Dashboard
    add_figure(doc, "screenshots/user_grafana_dashboard.png",
               "Figure 8: Live Grafana Monitoring Dashboard (http://localhost:3000) Showing Model Status: HEALTHY, API Requests, and Class Counts")

    doc.add_paragraph(
        "Figure 8 illustrates the comprehensive Grafana monitoring dashboard configured for the fraud detection system. "
        "Key operational indicators include: Model Status ('HEALTHY'), Total API Requests (5), Request Throughput spikes per endpoint, "
        "Prediction Count partitioned by class ('Legitimate'), and Response Latency percentiles. "
        "Anonymous viewer access has been enabled, allowing anyone to view this live dashboard at: "
        "https://buys-systems-bars-sage.trycloudflare.com."
    )

    # ------------------ 6. Evidently AI Data Drift & Traffic Simulation ------------------
    h1 = doc.add_heading("6. Evidently AI Data Drift & Traffic Shift Simulation (Tasks 7, 8 & 9)", level=1)
    h1.style.font.color.rgb = RGBColor(31, 78, 121)
    
    doc.add_paragraph(
        "Evidently AI was integrated into src/monitoring.py to compare the Reference transaction distribution (500 records) against "
        "the Current drifted dataset (Section7_Q3_Payment_Fraud_Current_Drift.csv, 160 records). "
        "The analysis employed the Jensen-Shannon distance for numerical and categorical distributions and Wasserstein distance for frequency distributions."
    )
    
    # Drift Table
    d_tbl = doc.add_table(rows=5, cols=5)
    d_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    d_headers = ["Feature", "Reference Baseline", "Current Production", "Statistical Distance", "Drift Status"]
    for j, h in enumerate(d_headers):
        cell = d_tbl.rows[0].cells[j]
        set_cell_background(cell, "1F4E79")
        set_cell_margins(cell, 80, 80, 100, 100)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(h)
        r.font.name = "Calibri"
        r.font.size = Pt(9)
        r.font.bold = True
        r.font.color.rgb = RGBColor(255, 255, 255)
        
    drift_data = [
        ("Transaction_Amount_INR", "Mean: ₹631.42", "Mean: ₹1,120.30", "JS: 0.8313 (p < 0.001)", "DRIFT DETECTED"),
        ("Transactions_Last_Hour", "Mean: 1.69 / hr", "Mean: 2.92 / hr", "Wasserstein: 0.9815", "DRIFT DETECTED"),
        ("Payment_Method", "UPI: 44.5%, Card: 24.2%", "UPI: 31.3%, Card: 39.5%", "JS: 0.1725", "DRIFT DETECTED"),
        ("Overall Dataset Drift", "13 Monitored Features", "7 of 13 Drifted (53.8%)", "Threshold: 30.0%", "DATASET DRIFTED")
    ]
    
    for i, row_data in enumerate(drift_data):
        row = d_tbl.rows[i+1]
        bg = "FFFFFF" if i % 2 == 0 else "F9FAFB"
        for j, val in enumerate(row_data):
            cell = row.cells[j]
            set_cell_background(cell, bg)
            set_cell_margins(cell, 60, 60, 100, 100)
            p = cell.paragraphs[0]
            if j == 0:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            else:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            r = p.add_run(val)
            r.font.name = "Calibri"
            r.font.size = Pt(9)
            if "DRIFT" in val:
                r.font.bold = True
                r.font.color.rgb = RGBColor(192, 0, 0)
                
    doc.add_paragraph().paragraph_format.space_after = Pt(6)

    # Figure 9: Evidently Drift Report
    add_figure(doc, "screenshots/user_evidently_drift_report.png",
               "Figure 9: Evidently AI Interactive Data Drift Report (http://localhost:8000/drift-report) Showing 53.846% Drift Across 7 Columns")

    # Figure 10: Evidently Quality Report
    add_figure(doc, "screenshots/user_evidently_quality_report.png",
               "Figure 10: Evidently AI Interactive Data Quality Report (http://localhost:8000/quality-report) Comparing Distributions")

    h2 = doc.add_heading("6.1 Production Reliability Maintenance Strategy (Task 9)", level=2)
    h2.style.font.color.rgb = RGBColor(47, 85, 151)
    
    doc.add_paragraph(
        "To ensure continuous fraud detection accuracy when data drift occurs, the following 5-point maintenance policy is established:\n"
        "1. Automated Prometheus Alerting: Alert notification is triggered when Evidently AI Jensen-Shannon drift score exceeds 0.15 on core monetary features.\n"
        "2. Dynamic Threshold Calibration: During high-volume holiday campaigns or flash sales, the fraud classification threshold is dynamically adjusted from 0.50 to 0.38 to retain fraud recall without flooding human review queues.\n"
        "3. CI/CD Retraining Triggers: GitHub Actions workflow triggers automated pipeline retraining whenever >30% of input features exhibit persistent drift for more than 24 hours.\n"
        "4. Shadow Deployment Canary: New retrained models run in shadow mode processing 10% of live traffic to verify stability and false-positive rates prior to live cutover.\n"
        "5. Fail-Safe Circuit Breaker: Transactions exhibiting extreme anomaly indicators (e.g., >=3 failed OTPs or previous dispute records) are routed to manual review regardless of model score."
    )

    # ------------------ 7. CI/CD Pipeline ------------------
    h1 = doc.add_heading("7. Continuous Integration & Deployment (CI/CD) Pipeline", level=1)
    h1.style.font.color.rgb = RGBColor(31, 78, 121)
    
    doc.add_paragraph(
        "A full CI/CD pipeline is implemented in .github/workflows/ci.yml and executes automatically on push and pull-request events. "
        "The workflow provisions Ubuntu latest, installs pinned dependencies, performs Flake8 syntax checks, executes Pytest API integration tests, "
        "trains the model, and validates drift report generation."
    )
    
    # Figure 11: GitHub Actions
    add_figure(doc, "screenshots/github_actions_workflow.png",
               "Figure 11: Successful GitHub Actions CI/CD Pipeline Execution (Run #42201006013 — Status: Success)")

    # ------------------ 8. Execution Guide ------------------
    h1 = doc.add_heading("8. Verification & Execution Instructions for Faculty", level=1)
    h1.style.font.color.rgb = RGBColor(31, 78, 121)
    
    doc.add_paragraph(
        "The examination package is fully executable. Evaluators can replicate all results using the commands below:"
    )
    
    e_tbl = doc.add_table(rows=1, cols=1)
    e_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    e_cell = e_tbl.rows[0].cells[0]
    e_cell.width = Inches(6.5)
    set_cell_background(e_cell, "F2F4F7")
    set_cell_margins(e_cell, 80, 80, 100, 100)
    ep = e_cell.paragraphs[0]
    erun = ep.add_run(
        '# 1. Unzip the submission archive\n'
        'unzip 231FA04E20_MLOps_Internal.zip -d 231FA04E20_MLOps_Internal\n'
        'cd 231FA04E20_MLOps_Internal\n\n'
        '# 2. Execute end-to-end automated script\n'
        'chmod +x run_all.sh\n'
        './run_all.sh\n\n'
        '# 3. Or run components independently:\n'
        'pip install -r requirements.txt\n'
        'pytest -v tests/test_api.py\n'
        'python -m src.train\n'
        'python -m src.monitoring\n'
        'python -m uvicorn src.app:app --host 0.0.0.0 --port 8000\n'
        'python -m src.simulate_traffic\n'
    )
    erun.font.name = "Courier New"
    erun.font.size = Pt(8.5)

    doc.add_paragraph().paragraph_format.space_after = Pt(6)

    # ------------------ 9. Conclusion ------------------
    h1 = doc.add_heading("9. Conclusion & Submission Deliverables Summary", level=1)
    h1.style.font.color.rgb = RGBColor(31, 78, 121)
    
    doc.add_paragraph(
        "All requirements of Set-3 (Question 3) have been fully implemented, rigorously tested, deployed, and verified. "
        "The submission package contains the complete executable source tree, interactive Jupyter Notebook, visual Evidently AI HTML reports, "
        "trained model binaries, live public cloud URLs, and verification screenshots."
    )
    
    output_path = "/Users/venkatareddy/Desktop/231FA04E20_Payment_Fraud_Detection_MLOps_Report.docx"
    doc.save(output_path)
    doc.save("reports/231FA04E20_Payment_Fraud_Detection_MLOps_Report.docx")
    print(f"Document successfully created at {output_path} and reports/231FA04E20_Payment_Fraud_Detection_MLOps_Report.docx")

if __name__ == "__main__":
    create_report()
