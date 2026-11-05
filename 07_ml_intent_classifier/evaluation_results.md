--- EVALUATION ON HELD-OUT TEST SET ---
              precision    recall  f1-score   support

 check_order       1.001.00      1.00       160
    escalate       1.001.00      1.00       160
     general       1.001.00      1.00       120

    accuracy          1.00       440
   macro avg       1.001.00      1.00       440
weighted avg       1.001.00      1.00       440


Confusion Matrix:
[[160   0   0]
 [  0 160   0]
 [  0   0 120]]
Model saved.

"""Current results show 1.00 Macro-F1. However, this is due to the synthetic nature of the dataset (template-based generation). Future work requires human-annotated, diverse natural language samples to test true generalization."""