# Insurance Conversational BI — Beginner-Friendly Prototype

## 1. What are we building?

We are building a small **Conversational BI application for insurance data**.

Normally, a BI user has to:

1. Open a dashboard.
2. Find a chart.
3. Apply filters.
4. Read the result.

Our application allows the user to simply type:

> "Show total claims by region."

The application uses an LLM (Llama-family model) to understand the question.

The LLM does **not directly touch the dataframe**.

Instead, it produces a small JSON plan such as:

```json
{
  "operation": "groupby",
  "group_by": "region",
  "metric": "claim_amount",
  "aggregation": "sum",
  "filters": []
}
```

Python then executes this plan against Pandas.

That is the key design idea.

---

# 2. The mental model

Remember this:

**User → Understand → Plan → Execute → Visualize → Explain**

Or:

```text
User
 |
 | "Show claims by region"
 v
Llama
 |
 | JSON plan
 v
Query Engine
 |
 | Pandas
 v
Result
 |
 +------> Table
 |
 +------> Chart
 |
 v
User
```

The LLM is the **brain that understands the business question**.

Pandas is the **calculator**.

Streamlit is the **screen/application**.

Plotly is the **visualization layer**.

---

# 3. Why not let Llama generate Python?

A beginner might try:

```text
User question
      |
      v
Llama
      |
      v
Python code
      |
      v
exec(python_code)
```

Do NOT start this way.

It can become unsafe and difficult to control.

Instead:

```text
User
 |
 v
Llama
 |
 v
Structured JSON
 |
 v
Your Python code
 |
 v
Pandas
```

This gives us much more control.

---

# 4. What is few-shot prompting?

Few-shot prompting means:

> "Show the LLM a few examples of what you expect before asking it a new question."

For example:

```text
User:
What is the total claim amount?

Assistant:
{
  "operation": "sum",
  "column": "claim_amount"
}
```

Another:

```text
User:
Show claims by region.

Assistant:
{
  "operation": "groupby",
  "group_by": "region",
  "metric": "claim_amount",
  "aggregation": "sum"
}
```

Then the model sees:

```text
User:
Show claims by region for diabetes members.
```

It can infer that it needs:

- group by region
- sum claim amount
- filter diagnosis = Diabetes

This is the basic idea of few-shot prompting.

---

# 5. Project architecture

```text
                 ┌──────────────┐
                 │     User     │
                 └──────┬───────┘
                        |
                        v
                ┌───────────────┐
                │   Streamlit   │
                │      UI       │
                └──────┬────────┘
                       |
                       v
                ┌───────────────┐
                │ Llama / LLM   │
                │ Few-shot      │
                │ Prompt        │
                └──────┬────────┘
                       |
                       v
                ┌───────────────┐
                │ JSON Query    │
                │ Plan          │
                └──────┬────────┘
                       |
                       v
                ┌───────────────┐
                │ Validation     │
                └──────┬────────┘
                       |
                       v
                ┌───────────────┐
                │ Query Engine  │
                │ Pandas        │
                └──────┬────────┘
                       |
              ┌────────┴────────┐
              v                 v
          Data Table          Chart
              |                 |
              └────────┬────────┘
                       v
                     User
```

---

# 6. What each file does

```text
app.py
```

This is the Streamlit application.

It:

- loads data
- displays basic EDA
- receives questions
- calls Llama
- executes the query
- displays the result

---

```text
src/llm.py
```

This is the LLM connection.

It talks to Hugging Face.

If later your company gives you an internal Llama API, this is one of the main files you would change.

---

```text
src/prompts.py
```

Contains the system prompt and few-shot examples.

This is where you teach the model:

> "When the user asks this type of question, produce this type of JSON."

---

```text
src/query_engine.py
```

This is the most important safety layer.

It checks:

- Is the operation allowed?
- Is the column allowed?
- Are filters allowed?

Then it executes Pandas.

---

```text
src/response_parser.py
```

LLMs sometimes return:

```text
```json
{
...
}
```
```

instead of pure JSON.

This file extracts the JSON safely enough for this prototype.

---

```text
src/charts.py
```

Converts query results into Plotly charts.

---

```text
data/insurance_data.csv
```

Sample insurance dataset.

You can replace this later with your real dataset.

---

# 7. How to run the project

## Step 1 — Open in VS Code

Open the folder:

```text
conversational_bi_insurance
```

---

## Step 2 — Create virtual environment

Windows:

```bash
python -m venv .venv
```

Activate:

```bash
.venv\Scripts\activate
```

---

## Step 3 — Install libraries

```bash
pip install -r requirements.txt
```

---

# 8. Getting a free LLM API

For this learning prototype, we use **Hugging Face Inference Providers**.

Hugging Face currently provides a small monthly free credit allowance for free users; the amount can change, so treat this as a learning/testing option rather than a guaranteed unlimited free service.

Official documentation:

Hugging Face Inference Providers:
https://huggingface.co/docs/inference-providers

Pricing/free-credit information:
https://huggingface.co/docs/inference-providers/en/pricing

---

# 9. Create Hugging Face account

Go to:

https://huggingface.co/

Create an account.

Then open:

https://huggingface.co/settings/tokens

Create a token with permission to make inference requests.

Copy the token.

---

# 10. Configure the project

You will see:

```text
.env.example
```

Copy it to:

```text
.env
```

Put your token inside:

```text
HF_TOKEN=hf_xxxxxxxxxxxxxxxxx
```

Do NOT commit `.env` to GitHub.

---

# 11. Select the model

The project initially uses:

```text
meta-llama/Llama-3.1-8B-Instruct
```

However, hosted model/provider availability can change.

If Hugging Face does not currently route that model for your account, go to the Hugging Face model/inference pages and choose an available instruct/chat model, then change:

```text
LLM_MODEL=...
```

in `.env`.

The rest of the project stays the same.

---

# 12. Run Streamlit

From the project folder:

```bash
streamlit run app.py
```

Your browser should open the application.

---

# 13. Try these questions

Start simple.

### Test 1

```text
How many members do we have?
```

Expected:

```text
COUNT(member_id)
```

---

### Test 2

```text
What is the total claim amount?
```

Expected:

```text
SUM(claim_amount)
```

---

### Test 3

```text
What is the average claim amount?
```

Expected:

```text
MEAN(claim_amount)
```

---

### Test 4

```text
Show total claims by region.
```

Expected:

```text
GROUP BY region
SUM claim_amount
```

The app should show a table and bar chart.

---

### Test 5

```text
Show claims by region for diabetes members.
```

Expected:

```text
FILTER:
diagnosis = Diabetes

GROUP BY:
region

METRIC:
claim_amount

AGGREGATION:
sum
```

---

### Test 6

```text
Show out-of-network claims by diagnosis.
```

Expected:

```text
FILTER:
provider_type = Out-of-Network

GROUP BY:
diagnosis

SUM:
claim_amount
```

---

### Test 7

```text
Show monthly claim trend.
```

Expected:

```text
claim_date
    |
    v
month
    |
    v
SUM(claim_amount)
    |
    v
Line chart
```

---

# 14. What happens when you ask a question?

Suppose you type:

```text
Show claims by region for diabetes members.
```

## Step 1 — Streamlit receives the question

```text
question =
"Show claims by region for diabetes members."
```

---

## Step 2 — Few-shot prompt is sent to Llama

Llama sees:

```text
You are an insurance BI assistant.

Available columns:
...

Example:
Show claims by region.

=> groupby region

Example:
Show diabetes claims.

=> filter diagnosis=Diabetes

Now answer:
Show claims by region for diabetes members.
```

---

# 15. Llama generates a plan

Something similar to:

```json
{
  "operation": "filter_groupby",
  "group_by": "region",
  "metric": "claim_amount",
  "aggregation": "sum",
  "filters": [
    {
      "column": "diagnosis",
      "operator": "equals",
      "value": "Diabetes"
    }
  ]
}
```

---

# 16. Python validates the plan

Python checks:

```text
Is filter_groupby allowed?
        YES

Is region an allowed column?
        YES

Is claim_amount an allowed column?
        YES

Is diagnosis an allowed column?
        YES
```

Only then is the operation executed.

---

# 17. Pandas executes the operation

Conceptually:

```python
df[
    df["diagnosis"] == "Diabetes"
]
```

then:

```python
.groupby("region")["claim_amount"].sum()
```

The user doesn't need to know any of this.

They simply ask:

> "Show diabetes claims by region."

---

# 18. Why this architecture is useful

You already know EDA and ML.

Your new learning is mainly:

```text
                 YOUR EXISTING SKILLS
                        |
                EDA + Python + ML
                        |
                        v
              Conversational BI
                        |
          ┌─────────────┼─────────────┐
          v             v             v
        LLM          Pandas/SQL    Streamlit
          |
          v
   Prompt Engineering
          |
          v
     Few-shot
          |
          v
   Structured Output
```

You do NOT need to relearn data science.

---

# 19. What you should learn next

Follow this order.

## Level 1 — LLM basics

Learn:

```text
LLM
Token
Context window
Temperature
System prompt
User prompt
Assistant prompt
Inference
```

---

## Level 2 — Prompt engineering

Learn:

```text
Zero-shot
Few-shot
Role prompting
Structured prompting
Output constraints
```

---

## Level 3 — Structured output

This is extremely important for BI.

Learn how to make an LLM produce:

```json
{
  "operation": "...",
  "column": "...",
  "filters": []
}
```

rather than free-form text.

---

## Level 4 — Tool/function calling

Eventually instead of:

```text
LLM
 ↓
JSON
 ↓
Python
```

you will have:

```text
LLM
 ↓
Tool selection
 ↓
Python function
```

Example:

```text
calculate_claims()
calculate_pmpm()
claims_by_region()
claims_trend()
```

This is highly relevant to Conversational BI.

---

# 20. Level 5 — Text-to-SQL

Your real insurance application will probably not keep millions of claims in a CSV.

It may eventually look like:

```text
User
 |
 v
Llama
 |
 v
SQL
 |
 v
SQL validation
 |
 v
Data warehouse
 |
 v
Result
 |
 v
Llama
 |
 v
Answer
```

You should therefore learn **Text-to-SQL**.

---

# 21. Level 6 — Conversation memory

Currently the prototype treats each question independently.

Eventually:

```text
User:
Show claims by region.

Assistant:
...

User:
Only diabetes.

Assistant:
...
```

The second question requires the application to remember the first query.

Then:

```text
Conversation history
        |
        v
      Llama
        |
        v
Current intent
```

---

# 22. Level 7 — RAG

Do NOT start with RAG.

RAG becomes important when you want to answer questions from documents.

Example:

```text
"What does our OON reimbursement policy say?"
```

Now you need:

```text
Documents
   |
Chunking
   |
Embeddings
   |
Vector DB
   |
Relevant documents
   |
Llama
   |
Answer
```

For pure numerical BI questions, Pandas/SQL is more important than RAG.

---

# 23. Insurance Conversational BI — advanced version

Eventually your project can become:

```text
                         USER
                           |
                           v
                    Conversation
                       Manager
                           |
                           v
                         Llama
                           |
             ┌─────────────┼──────────────┐
             |             |              |
             v             v              v
         BI Tool        EDA Tool       RAG Tool
             |             |              |
             v             v              v
          SQL/Pandas    Statistics     Documents
             |             |              |
             └─────────────┼──────────────┘
                           |
                           v
                    Result Validator
                           |
                           v
                       Llama
                           |
                           v
                       Answer
```

This is the architecture you should ultimately understand.

---

# 24. What I would build after this prototype

Once this works, add these capabilities in this order:

```text
Phase 1
✓ Dataset upload
✓ Basic EDA
✓ Few-shot Llama
✓ Structured JSON
✓ Pandas execution
✓ Charts

Phase 2
✓ Filters
✓ Date ranges
✓ Multiple filters
✓ Follow-up questions
✓ Conversation memory

Phase 3
✓ Tool/function calling
✓ SQL
✓ SQL validation
✓ Large datasets

Phase 4
✓ Insurance business metrics
✓ PMPM
✓ OON %
✓ Claim frequency
✓ Claim severity
✓ Member risk analysis

Phase 5
✓ RAG
✓ Insurance policy documents
✓ Explainability
✓ Evaluation
✓ Guardrails
✓ Logging
✓ Monitoring
```

---

# 25. Most important lesson

Don't think:

> "I need to learn Llama."

Think:

> **"I need to build a controlled interface between natural language and data."**

The LLM is only one component.

The real system is:

```text
Natural Language
       ↓
LLM
       ↓
Intent / Query Plan
       ↓
Validation
       ↓
Data Engine
       ↓
Statistics
       ↓
Visualization
       ↓
Natural Language
```

That is **Conversational BI**.

---

# 26. Your project files

The prototype contains:

```text
conversational_bi_insurance/
│
├── app.py
├── README_1.md
├── requirements.txt
├── .env.example
│
├── data/
│   └── insurance_data.csv
│
└── src/
    ├── config.py
    ├── llm.py
    ├── prompts.py
    ├── query_engine.py
    ├── response_parser.py
    └── charts.py
```

You can start with this project and gradually replace each layer with the technology used by your organization's actual application.

