# Media Tracker

[Leer en Español](README.es.md)

**Media Tracker** is a personal collection of movies, series, and games that I have consumed. It serves as a digital log to track and review my entertainment history.

## Technologies

This project is built using:
- **[Hugo](https://gohugo.io/):** A fast and flexible static site generator.
- **[hugo-blog-awesome](https://github.com/hugo-sid/hugo-blog-awesome):** A clean and minimal theme for Hugo.
- **[Obsidian](https://obsidian.md/):** Used for creating and editing notes conveniently.

## Setup & Usage

To run this project locally, ensure you have Hugo installed.

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd MediaTracker
    ```

2.  **Run the development server:**
    ```bash
    hugo server -D
    ```
    The site will be available at `http://localhost:1313/`.

3.  **Build for production:**
    ```bash
    hugo
    ```
    The static files will be generated in the `public/` directory.

## Content Management & Workflow

Content is managed using Markdown files located in the `content/` directory. The primary workflow involves editing notes in **Obsidian** and then migrating them to Hugo.

### 🔄 Obsidian to Hugo Migration

This project uses a custom migration script (`scripts/migration.py`) to transform Obsidian notes into Hugo-compatible content.

- **Source of Truth:** Obsidian Vault. Use Obsidian for all note creation and editing.
- **Migration:** Run the `scripts/migration.py` script to generate Hugo content.
  - This process handles WikiLinks conversion, image processing, and frontmatter adjustments.
- **Immutability:** The `content/` directory in this Hugo project should be treated as **immutable** for manual edits. It is a generated copy. Any manual changes here will be overwritten by the next migration.

### 📡 RSS Feeds

The site provides the following RSS feeds:

- **All Content:** [`index.xml`](index.xml) - Contains all movies, series, and games.
- **Finished Items:** [`acabados/index.xml`](acabados/index.xml) - specific feed for items marked as "Acabado" (Finished).
