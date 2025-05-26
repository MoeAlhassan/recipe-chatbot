## Part 1: Define Dimensions & Generate Initial Queries

1.  **Identify Key Dimensions:**  

    * **Identify 3‑4 key dimensions relevant to your Recipe Bot's functionality and potential user inputs.**  
        * **Answer:** `(available_ingredients, dietary_restriction, max_total_time, desired_cuisine)`

    * **For each dimension, list at least 3 example values.**  
        * **available_ingredients:** chicken breast, tofu, salmon fillet, broccoli  
        * **dietary_restriction:** vegan, gluten‑free, nut allergy, none  
        * **max_total_time:** 15 minutes, 30 minutes, 45 minutes  
        * **desired_cuisine:** Italian, Thai, Comfort food, Breakfast  

2.  **Generate Unique Combinations (Tuples):**
    * **Prompt for the LLM:**  
      ```
      I am designing test cases for a recipe chatbot. The bot generates recipes based on the following user input dimensions:
      
        1.  available_ingredients: (e.g. chicken breast, tofu, salmon fillet, broccoli)
        2.  dietary_restriction: (e.g. vegan, gluten‑free, nut allergy, none)
        3.  max_total_time: (e.g. 15 minutes, 30 minutes, 45 minutes)
        4.  desired_cuisine: (e.g. Italian, Thai, Comfort food, Breakfast)
      
      Please generate 15–20 unique combinations (tuples), where each tuple consists of one value from each dimension. Each combination should be realistic and diverse, covering a range of possible user scenarios. Present the output as a list of tuples, with each tuple in the following format:
      
      (available_ingredients; dietary_restriction; max_total_time; desired_cuisine)
      
      For example: (chicken breast, potatoes, broccoli; gluten-free; 30 minutes; Italian)

      Please ensure that the combinations are varied and do not repeat the same set of values.
      ```

3.  **Generate Natural Language User Queries:**
    *   Write a second prompt for an LLM to take 5-7 of the generated tuples and create a natural language user query for your Recipe Bot for each selected tuple.
    *   Review these generated queries to ensure they are realistic and representative of how a user might interact with your bot.

    **Answer:** Here are six realistic user queries derived from the sample tuples:

    1. **Mediterranean, gluten‑free, 30 min**  
       “I’ve got chicken breast, zucchini, and some cherry tomatoes. Can you suggest a Mediterranean‑style dinner that’s gluten‑free and takes about 30 minutes?”

    2. **Thai, vegan, 20 min**  
       “Could you give me a quick Thai vegan recipe I can whip up in 20 minutes using tofu, bell peppers, and spinach?”

    3. **Breakfast, gluten‑free, 10 min**  
       “What’s a fast gluten‑free breakfast I can make in 10 minutes with oats, almond milk, and blueberries?”

    4. **Italian, nut‑free, 15 min**  
       “I’m allergic to nuts and have whole‑wheat pasta, spinach, and mushrooms. Any way to put together a 15‑minute Italian dish?”

    5. **European, dairy‑free, 30 min**  
       “Please suggest a dairy‑free European‑style recipe that uses cod fillet, potatoes, and green beans and can be ready in 30 minutes.”

    6. **Japanese comfort, nut‑free, 35 min**  
       “I’m craving a cozy Japanese comfort dish. I have ramen noodles, tofu, and spinach, but I’m allergic to nuts. Something that cooks in around 35 minutes would be great.”

   ~~**Alternative for Query Generation:** If you prefer to skip the LLM-based query generation (steps 2 and 3 above), you may use the pre-existing queries and bot responses found in `homeworks/hw2/results_20250518_215844.csv` as the basis for your error analysis in Part 2. You can then proceed directly to the "Open Coding" step using this data.~~

## Part 2: Initial Error Analysis (Ref Sec 3.2, 3.3, 3.4 of relevant course material)

1.  **Run Bot on Synthetic Queries:**
    *   Execute your Recipe Bot using the synthetic queries generated in Part 1.
    *   Record the full interaction traces for each query.

2.  **Open Coding:** (an initial analysis step where you review interaction traces, assigning descriptive labels/notes to identify patterns and potential errors without preconceived categories, as detailed in Sec 3.2 of the provided chapter)
    *   Review the recorded traces.
    *   Perform open coding to identify initial themes, patterns, and potential errors or areas for improvement in the bot's responses.

3.  **Axial Coding & Taxonomy Definition:** (a follow-up step where you group the initial open codes into broader, structured categories or 'failure modes' to build an error taxonomy, as described in Sec 3.3 of the provided chapter)
    *   Group the observations from open coding into broader categories or failure modes.
    *   For each identified failure mode, create a clear and concise taxonomy. This should include:
        *   **A clear Title** for the failure mode.
        *   **A concise one-sentence Definition** explaining the failure mode.
        *   **1-2 Illustrative Examples** taken directly from your bot's behavior during the tests. If a failure mode is plausible but not directly observed, you can provide a well-reasoned hypothetical example.

        | # | **Failure‑Mode Title** | One‑Sentence Definition | Illustrative Example(s) |
        |---|------------------------|-------------------------|-------------------------|
        | **1** | **allergen_present** | The recipe includes an ingredient that violates the user’s stated allergy or dietary restriction. | **Observed:** Gluten‑free user received soy sauce containing wheat.<br>**Hypo:** Nut‑allergic user is told to add crushed peanuts. |
        | **2** | **no_substitution** | The bot respects the restriction but fails to suggest an obvious safe alternative. | **Observed:** Suggests regular soy sauce instead of gluten‑free tamari in a “GF” recipe.<br>**Hypo:** Uses dairy cheese without offering plant‑based cheese in a vegan request. |
        | **3** | **missing_prep_detail** | Essential prep instructions (slice thickness, soaking, pressing, etc.) are omitted or too vague to follow confidently. | **Observed:** “Slice zucchini” with no thickness guidance.<br>**Hypo:** “Press tofu” with no time or weight specified. |
        | **4** | **serving_size** | The bot leaves unclear—or wrongly assumes—how many portions the recipe yields or how much of each ingredient to use. | **Observed:** Returns 2 lbs of chicken for a single‑serve request without explaining portions.<br>**Hypo:** “Makes 12 cookies” when user asked for dessert for two. |
        | **5** | **passive_time_hidden** | The stated “total time” ignores passive waits like chilling, marinating, or resting, causing the user to exceed their limit. | **Observed:** 30‑min request includes “bake 25 min” plus “cool 25 min” not counted.<br>**Hypo:** 15‑min salad requires quinoa “cool completely” (~30 min). |



4.  **[Optional] Spreadsheet for Analysis:**
    *   Create a spreadsheet to systematically track your error analysis.
    *   Include the following columns:
        *   `Trace_ID` (a unique identifier for each interaction)
        *   `User_Query` (the query given to the bot)
        *   `Full_Bot_Trace_Summary` (a summary of the bot's full response and behavior)
        *   `Open_Code_Notes` (your notes and observations from the open coding process)
        *   A column for each of your 3-5 defined `Failure_Mode_Title`s (use 0 or 1 to indicate the presence or absence of that failure mode in the trace).

---

**Note:** You have the flexibility to edit, create, or modify any files within the assignment structure as needed to fulfill the requirements of this homework. This includes, but is not limited to, the `failure_mode_taxonomy.md` file, scripts for running your bot, or any spreadsheets you create for analysis. 