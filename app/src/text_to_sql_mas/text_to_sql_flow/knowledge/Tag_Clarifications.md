
Here’s a structured breakdown of the CDM domains **Observation**, **Measurement**, and **Condition**, based on OMOP documentation and expert forum discussions:

---

## ✅ Observation

* **Definition**: Captures clinical or contextual facts **not** derived from standardized tests or explicit disease processes—e.g., family history, self-reported lifestyle, allergies, survey or questionnaire responses ([medical-data-models.org][1]).
* **When to use**: Data that arise from examination, questioning, social context, or free-text entries; also things that don’t fit elsewhere such as “does the patient smoke?” ([medical-data-models.org][1]).
* **Data model**: Stored as name/value pairs with flexible types: numeric (`value_as_number`), concept (`value_as_concept_id`), string, or datetime ([medical-data-models.org][1]).

---

## 📊 Measurement

* **Definition**: Quantitative or qualitative results **from standardized tests or instruments**, e.g., lab values, vital signs, imaging tests—each record represents an actual measurement or test execution ([ohdsi.org][2]).
* **When to use**: Requires a test or instrument-driven process, even if result is qualitative (e.g., +/– immunoassay) ([ohdsi.org][2]).
* **Data model**: Captures both attribute (what was measured) and result (numeric or coded concept) with units, and can indicate if the test was performed even without a value .

---

## 🩺 Condition

* **Definition**: Represents clinically significant diagnoses or disease conditions that a patient has experienced—intended for medical diagnoses ([medical-data-models.org][1]).
* **When to use**: Whenever there's an ongoing or acute condition, sign/symptom, or diagnosis. Even if represented in source data via ICD/SNOMED, map to **Condition** when it indicates active disease ([ohdsi.github.io][3]).
* **Data model**: Each row indicates a patient “had” the condition at a certain time; no storing of absence or “negatives” – OMOP assumes absence of a record = absence of condition ([forums.ohdsi.org][4]).

---

### 🗂️ Comparison Table

| Feature              | **Observation**                                         | **Measurement**                       | **Condition**                           |
| -------------------- | ------------------------------------------------------- | ------------------------------------- | --------------------------------------- |
| **Data source**      | Questioning, ideation, non-test facts                   | Standard test or instrument           | Diagnostic/asserted condition           |
| **Use cases**        | Survey answers, family history, lifestyle               | Lab results, vitals, instrument tests | Diagnoses, symptoms, clinical condition |
| **Data type**        | name/value pairs (concept/string/number/datetime)       | numeric or coded result, units        | condition concept with dates            |
| **Negative values?** | Supports explicit “No” values via `value_as_concept_id` | Possible but rare                     | Not allowed—omission indicates absence  |

---

### 🔬 Forum Insight

From OHDSI forums:

* **Measurements** always require a test to generate the fact; **Observations** generally do not ([ohdsi.org][2]).
* Complex “question/answer” EAV data (e.g. surveys) may land in Observation or Measurement depending on context ([forums.ohdsi.org][5]).
* Recording a condition's **absence** (like “no hypertension”) is done in *Observation* with value indicating absence—not in Condition ([forums.ohdsi.org][5]).

---

### 🧭 When to Choose Which

1. **Patient answers “Do you smoke?” → Observation** (self-reported)
2. **Lab test: serum glucose = 120 mg/dL → Measurement**
3. **EHR diagnosis: Type 2 diabetes → Condition**

---

### 📚 Want more?

* OMOP wiki documentation for **Measurement** and **Observation** tables is excellent ([ohdsi.github.io][3], [ohdsi.org][2]).
* OHDSI forums offer lively discussions on borderline cases and ETL best practices ([forums.ohdsi.org][6]).

Let me know if you'd like examples from real ETL scripts or need help mapping your specific data!

[1]: https://medical-data-models.org/35105?utm_source=chatgpt.com "OMOP Common Data Model (CDM) Observation - Portal of Medical ..."
[2]: https://www.ohdsi.org/web/wiki/doku.php?id=documentation%3Acdm%3Ameasurement&utm_source=chatgpt.com "documentation:cdm:measurement [Observational Health Data ..."
[3]: https://ohdsi.github.io/CommonDataModel/cdm54.html?utm_source=chatgpt.com "OMOP CDM v5.4 - GitHub Pages"
[4]: https://forums.ohdsi.org/t/negative-information-in-omop-cdm/4923?utm_source=chatgpt.com "Negative information in OMOP CDM - Researchers - OHDSI Forums"
[5]: https://forums.ohdsi.org/t/how-to-handle-eav-variable-value-pairs-in-measurement-or-observation-call-for-input-from-the-community/13905?utm_source=chatgpt.com "How to handle EAV variable/value pairs in MEASUREMENT or ..."
[6]: https://forums.ohdsi.org/t/what-makes-observations-distinct-from-measurements-or-disorders/8093?utm_source=chatgpt.com "What makes observations distinct from measurements or disorders?"
