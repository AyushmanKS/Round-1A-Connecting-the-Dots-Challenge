# Connecting the Dots Challenge - Round 1A Submission

This repository contains the solution for Round 1A, which focuses on high-accuracy, structured outline extraction from PDF documents. The goal is to produce a clean, hierarchical outline (Title, H1, H2, H3) that can serve as a reliable foundation for further document analysis.

## Core Methodology

The primary challenge with PDF structure extraction is the unreliability of simple heuristics like font size alone. This solution addresses that challenge by implementing a robust, **style-based ranking engine** that dynamically learns the specific "design language" of each document.

The approach is executed in three main stages:

1.  **Style Analysis and Cataloging:** The script first performs a full analysis of the document to build a comprehensive catalog of every font style present (a combination of font size and weight). It calculates the frequency of each style, allowing it to accurately identify the style most likely representing the main body text, which serves as a baseline.

2.  **Heading Identification and Ranking:** Any style that is more prominent (e.g., larger or bolder) than the identified body text is classified as a potential heading style. These candidate styles are then **ranked** from most prominent to least. This ranking is used to create a dynamic mapping: the top-ranked style is assigned to `H1`, the second-ranked to `H2`, and all subsequent heading styles to `H3`.

3.  **Hierarchical Structuring and Output:** With the style-to-level map established, the script performs a final pass through the document. It classifies each text block according to the map and adds it to the outline. A final correction step ensures the hierarchy is logical (e.g., an H2 will not appear before the first H1). The resulting list of headings is then formatted into the required JSON structure.

This methodology makes the solution highly adaptive and accurate, capable of handling a wide variety of PDF layouts, including those with unconventional or inconsistent formatting.

## Technology Stack

*   **Libraries**:
    *   `PyMuPDF (fitz)`: This library was chosen for its exceptional performance and its ability to extract detailed text metadata, including font size, name, and precise coordinates. This low-level access is critical for the style analysis engine to function correctly and meet the challenge's time constraints.
    *   `os`, `json`: Standard Python libraries were used for file system interactions and for generating the final JSON output file according to the specified schema.

*   **Models**:
    *   No pre-trained machine learning models were used in this solution. The approach is purely algorithmic, ensuring full compliance with the strict model size and offline execution constraints.

## Project Setup and Execution

The project is containerized with Docker and is designed to run offline without any network access at runtime.

### 1. Build the Docker Image

Ensure Docker is installed and running. Navigate to the root directory of this project in your terminal and execute the following command:

```sh
docker build --platform linux/amd64 -t mysolution-1a .
```
### 2. Run the Solution

Place any PDF files you wish to process into the input directory. Then, execute the following command from the project root. The script will automatically process all PDFs found in the /app/input directory and save the corresponding structured JSON files to the /app/output directory.
```sh
docker run --rm -v $(pwd)/input:/app/input -v $(pwd)/output:/app/output --network none mysolution-1a
```

