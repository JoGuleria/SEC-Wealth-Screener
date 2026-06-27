\# SEC Wealth Screener



SEC Wealth Screener is a public-data wealth screening tool that uses SEC insider ownership filings to identify visible public-equity capacity signals.



The tool processes SEC Form 3, Form 4, and Form 5 insider transaction data, classifies reporting owners as individuals or entities, calculates transaction-based wealth signals, and displays ranked results in a Streamlit dashboard.



\## Purpose



The goal of this project is to build a lightweight wealth screening workflow using public SEC data.



This project does \*\*not\*\* estimate total net worth. Instead, it identifies people and entities with visible public-equity activity that may indicate financial capacity.



\## Features



\* Parses SEC insider transaction data

\* Extracts reporting owners, companies, tickers, and transaction details

\* Calculates reported transaction values

\* Separates individuals from entities, trusts, funds, and holding companies

\* Classifies transaction types such as sales, purchases, grants, gifts, and option exercises

\* Creates a public-equity capacity signal score

\* Assigns capacity tiers

\* Explains why each record surfaced

\* Provides a Streamlit dashboard for filtering and review



\## Tech Stack



\* Python

\* Pandas

\* NumPy

\* Streamlit

\* SEC Form 3/4/5 Insider Transactions Data



\## Project Structure



```text

SEC-Wealth-Screener/

│

├── app.py

├── requirements.txt

├── README.md

│

├── src/

│   └── build\_scores.py

│

└── data/

&#x20;   ├── raw/

&#x20;   └── processed/

&#x20;       └── sec\_capacity\_scores.csv

```



\## How It Works



1\. SEC insider transaction data is downloaded as a quarterly ZIP file.

2\. The pipeline reads key SEC files:



&#x20;  \* `SUBMISSION.tsv`

&#x20;  \* `REPORTINGOWNER.tsv`

&#x20;  \* `NONDERIV\_TRANS.tsv`

3\. The data is merged using accession numbers.

4\. Transaction value is calculated as:



```text

transaction\_value = trans\_shares × trans\_pricepershare

```



5\. Reporting owners are classified as either:



&#x20;  \* Individual

&#x20;  \* Entity



6\. Transaction codes are grouped into readable categories:



&#x20;  \* Open Market Purchase

&#x20;  \* Open Market Sale

&#x20;  \* Grant/Award

&#x20;  \* Option Exercise

&#x20;  \* Gift

&#x20;  \* Tax/Withholding

&#x20;  \* Other



7\. A capacity signal score is created using:



&#x20;  \* Total reported transaction value

&#x20;  \* Open-market transaction value

&#x20;  \* Largest transaction value

&#x20;  \* Filing activity

&#x20;  \* Role strength

&#x20;  \* Owner type



8\. The final results are displayed in a Streamlit dashboard.



\## Running the Project Locally



Install dependencies:



```bash

pip install -r requirements.txt

```



Build the scored dataset:



```bash

python src/build\_scores.py

```



Run the Streamlit app:



```bash

streamlit run app.py

```



\## Output



The scoring pipeline creates:



```text

data/processed/sec\_capacity\_scores.csv

```



The dashboard displays:



\* Ranked wealth signals

\* Individual/entity filters

\* Company and ticker search

\* Capacity tiers

\* Transaction values

\* Role scores

\* Explanation for why each record surfaced



\## Important Limitations



This tool is a public-data wealth screening aid, not a net-worth estimator.



It does not capture:



\* Private company ownership

\* Real estate wealth

\* Inherited wealth

\* Private investments

\* Full portfolio value

\* Education or school affiliation

\* Philanthropic affinity

\* Actual giving likelihood



SEC filings are only one public wealth signal. A high score should be interpreted as a reason for further research, not as a definitive measure of wealth or giving capacity.



\## Ethical Use



This project should only be used for research and analytical purposes.



It should not be used for:



\* Credit decisions

\* Housing decisions

\* Employment decisions

\* Insurance decisions

\* Eligibility screening

\* Any consumer decision-making purpose



\## Future Improvements



Potential next steps:



\* Store historical SEC records in SQLite

\* Automatically ingest new quarterly SEC files

\* Add historical trend analysis by person and company

\* Add real estate enrichment

\* Add IRS 990-PF/private foundation signals

\* Add FEC political giving signals

\* Add confidence scoring

\* Add charts and summary analytics

\* Add a methodology page inside the app



\## Project Status



MVP complete.



Current version supports SEC-based public-equity wealth screening using one quarterly SEC insider transaction dataset.



