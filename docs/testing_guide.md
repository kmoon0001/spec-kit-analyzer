# Manual Testing Guide

This document outlines the steps for manually testing the functionality of the Spec-Kit-Analyzer application.

## Adjudication Panel UI Test

**Objective:** To verify the functionality of the Adjudication panel for reviewing and resolving disagreements between NER models.

**Prerequisites:**
1.  Run an analysis on a document that is known to produce NER disagreements. This will populate the adjudication queue. You can achieve this by running an analysis with the "NER Ensemble" feature enabled in the Admin settings.
2.  Ensure there are items in the adjudication queue before starting the test.

**Test Steps:**

1.  **Open the Adjudication Tab:**
    *   Launch the application.
    *   Click on the "Adjudication" tab.
    *   **Expected Result:** The Adjudication panel is displayed. The table of items might be empty initially. The review panel at the bottom should be disabled.

2.  **Refresh the Queue:**
    *   Click the "Refresh Queue" button.
    *   **Expected Result:** The table populates with any pending adjudication items. The log should indicate that the queue was refreshed and how many items were found. If no items are found, the table should be empty.

3.  **Select an Item:**
    *   Click on a row in the adjudication items table.
    *   **Expected Result:**
        *   The "Review Selected Disagreement" group box at the bottom becomes enabled.
        *   The "Text" label is populated with the text snippet that the models disagreed on.
        *   The radio buttons are populated with the labels predicted by Model A and Model B. For example, "Confirm 'problem' (biobert)".
        *   All decision radio buttons are initially unchecked.
        *   The "Corrected Label" text box is disabled.

4.  **Test "Neither is Correct" Option:**
    *   Click the "Neither is Correct" radio button.
    *   **Expected Result:** The "Corrected Label" text input becomes enabled.
    *   Click one of the "Confirm" radio buttons again.
    *   **Expected Result:** The "Corrected Label" text input becomes disabled again.

5.  **Save a Decision (Confirm):**
    *   Select an item from the table.
    *   Select one of the "Confirm Model A" or "Confirm Model B" radio buttons.
    *   Optionally, add some text to the "Notes" field.
    *   Click the "Save Adjudication" button.
    *   **Expected Result:**
        *   A success message box appears.
        *   The item you just adjudicated is removed from the table.
        *   The review panel at the bottom is reset to its disabled/default state.

6.  **Save a Decision (Reject Both):**
    *   Select another item from the table.
    *   Select the "Neither is Correct" radio button.
    *   Enter a new label (e.g., "new_test_label") in the "Corrected Label" text box.
    *   Click the "Save Adjudication" button.
    *   **Expected Result:**
        *   A success message box appears.
        *   The item is removed from the table.

7.  **Verify Input Validation:**
    *   Select an item.
    *   Click "Save Adjudication" without making a decision.
    *   **Expected Result:** An error message appears asking you to select a decision.
    *   Select "Neither is Correct" but leave the "Corrected Label" field blank. Click "Save Adjudication".
    *   **Expected Result:** An error message appears asking you to provide a corrected label.

This concludes the manual test for the adjudication panel.
