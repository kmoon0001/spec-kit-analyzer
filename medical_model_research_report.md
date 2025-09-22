# Research Report: Lightweight, Medical-Grade AI Models

## Objective
This report identifies and evaluates state-of-the-art, lightweight, and efficient AI models for a clinical healthcare compliance application. The goal is to find replacements for existing models that are smaller, faster, and have lower computational overhead, without sacrificing accuracy. The models must be suitable for deployment in an offline, resource-constrained environment.

## 1. Named Entity Recognition (NER) Models

### Recommended Model: `OpenMed/OpenMed-NER-PathologyDetect-PubMed-v2-109M`

*   **Hugging Face Model Card:** [https://huggingface.co/OpenMed/OpenMed-NER-PathologyDetect-PubMed-v2-109M](https://huggingface.co/OpenMed/OpenMed-NER-PathologyDetect-PubMed-v2-109M)
*   **Key Characteristics:**
    *   **Size:** 109 million parameters ("Compact"). This is the smallest model in the OpenMed collection, making it ideal for resource-constrained environments.
    *   **Performance:** Achieves a high F1 score of 0.911 on the NCBI-Disease dataset.
    *   **Domain:** Specifically fine-tuned for pathology and disease detection on a corpus of PubMed abstracts.
    *   **Compatibility:** Fully compatible with the Hugging Face `transformers` library and the Python ecosystem.

### Other Candidates:

*   The **OpenMed NER collection** ([https://huggingface.co/OpenMed](https://huggingface.co/OpenMed)) offers over 380 models of various sizes and for different medical domains. If the recommended model is not suitable, other models from this collection can be considered.

## 2. Retrieval-Augmented Generation (RAG) Components

### Retriever: `pritamdeka/S-PubMedBert-MS-MARCO`

*   **Hugging Face Model Card:** [https://huggingface.co/pritamdeka/S-PubMedBert-MS-MARCO](https://huggingface.co/pritamdeka/S-PubMedBert-MS-MARCO)
*   **Key Characteristics:**
    *   **Base Model:** `microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract-fulltext` (110M parameters).
    *   **Fine-tuning:** Fine-tuned on the MS-MARCO dataset for information retrieval tasks.
    *   **Efficiency:** As a BERT-base model, it offers a good balance between performance and computational cost.
    *   **Compatibility:** Works seamlessly with the `sentence-transformers` library, which is the standard for sentence embedding tasks.

### Generator: `nabilfaieaz/tinyllama-med-full`

*   **Hugging Face Model Card:** [https://huggingface.co/nabilfaieaz/tinyllama-med-full](https://huggingface.co/nabilfaieaz/tinyllama-med-full)
*   **Key Characteristics:**
    *   **Base Model:** `TinyLlama/TinyLlama-1.1B-Chat-v1.0` (1.1 billion parameters). While larger than the NER and retriever models, this is very small for a capable LLM.
    *   **Quantization:** The model can be quantized to 4-bit, which significantly reduces its memory footprint and makes it suitable for offline deployment.
    *   **Fine-tuning:** Fine-tuned on a medical question-answering dataset (`ofir408/MedConceptsQA`).
    *   **Intended Use:** Designed to provide concise, factual answers, which is ideal for a RAG system.
    *   **Safety:** Includes a feature to warn users to seek professional medical advice.

## 3. General LLM/GPT Models

### Recommended Model: `nabilfaieaz/tinyllama-med-full`

*   **Hugging Face Model Card:** [https://huggingface.co/nabilfaieaz/tinyllama-med-full](https://huggingface.co/nabilfaieaz/tinyllama-med-full)
*   **Key Characteristics:**
    *   This model is also the best candidate for a general-purpose medical LLM. Its instruction-based fine-tuning allows it to handle a variety of tasks, including summarization and text generation, with appropriate prompting.
    *   Its small size and quantizability make it a versatile choice for a variety of tasks in a resource-constrained environment.

## Summary and Conclusion

This research has identified several state-of-the-art, lightweight, and efficient AI models for a clinical healthcare compliance application. The recommended models are all available on the Hugging Face hub and are compatible with the `transformers` library and the broader Python ecosystem.

By leveraging these models, it is possible to build a high-performance, offline-capable application with a significantly smaller computational footprint than would be possible with larger, more general-purpose models.
