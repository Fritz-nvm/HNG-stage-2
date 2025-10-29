----

# 🌍 HNG Stage 2: Country Data Service

A high-performance backend service built with **FastAPI** and **Clean Architecture** principles. This service manages country data, currency exchange rates, and generates a dynamic summary image, with a focus on speed through asynchronous I/O and optimized database operations.

## ✨ Features

  * **Clean Architecture:** Strict separation between the Domain, Application, and Infrastructure layers.
  * **High Performance:** Achieves refresh times in **seconds** (down from 10+ minutes) using `async/await` (with `httpx`) and SQLAlchemy's **bulk persistence** methods.
  * **Dynamic Data:** Fetches country data from REST Countries and currency rates from an external Exchange Rate API.
  * **Data Persistence:** Uses **SQLAlchemy** (with a persistent `sqlite` file) to store and query all country data.
  * **Image Generation:** Generates a dynamic summary image (`summary.png`) using **Pillow** to display statistics.

-----

## 🛠️ Technology Stack

| Category | Tools |
| :--- | :--- |
| **Framework** | FastAPI, Uvicorn |
| **Architecture** | Clean Architecture (Ports & Adapters), Dependency Injection (DI) |
| **Database** | SQLAlchemy ORM, SQLite |
| **Networking** | `httpx` (Asynchronous HTTP Client) |
| **External APIs** | REST Countries, Open Exchange Rates |
| **Image** | Pillow (PIL) |
| **Testing** | `pytest` (Recommended but not shown) |

-----

## 🚀 Getting Started

### Prerequisites

1.  **Python 3.10+**
2.  **API Keys:**
      * **`COUNTRIES_API_URL`**: Base URL for the REST Countries API (e.g., `https://restcountries.com/v3.1/all`).
      * **`EXCHANGE_RATE_API_URL`**: Base URL for the Exchange Rate API (e.g., `https://api.exchangerate-api.com/v4/latest/USD`).

### 1\. Setup

Clone the repository and install dependencies:

```bash
git clone https://github.com/Fritz-nvm/HNG-stage-2
cd HNG-stage-2
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
```

### 2\. Configure Environment

Create a file named **`.env`** in the project root and add your API configurations:

```env
# .env file content
COUNTRIES_API_URL="https://restcountries.com/v3.1/all"
EXCHANGE_RATE_API_URL="<Your Exchange Rate API URL here>"
DATABASE_URL="sqlite:///./data/countries.db"
# Ensure your database directory exists:
# mkdir -p data
```

### 3\. Run the Application

Start the Uvicorn server:

```bash
uvicorn main:app --reload
# Access the API at http://127.0.0.1:8000
```

-----

## 💡 Usage and Endpoints

### 1\. Refresh Data (Crucial First Step)

This endpoint executes the core business logic: fetching data, calculating GDP, performing bulk database writes, and generating the summary image.

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| **`POST`** | `/countries/refresh` | Fetches, processes, and persists all country data. **Must be run once before GET endpoints.** |

### 2\. Data Retrieval

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| **`GET`** | `/countries` | Lists all countries. Supports filtering by `region` and `currency`, and sorting by `gdp_desc` or `pop_desc`. |
| **`GET`** | `/countries/{name}` | Retrieves a single country record by full name. |
| **`GET`** | `/status` | Returns the total count of stored countries and the `last_refreshed_at` timestamp. |
| **`GET`** | `/countries/image` | **Serves the generated `summary.png` image.** |

### 3\. Management

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| **`DELETE`** | `/countries/{name}` | Deletes a country record by name. |

-----

## 🏗️ Architecture Highlights

### The Performance Secret

The `/countries/refresh` endpoint achieves its speed by employing two core optimization techniques:

1.  **Asynchronous I/O (`asyncio/httpx`):** All external network calls (fetching countries and currency rates) are executed using non-blocking asynchronous clients.
2.  **Consolidated Exchange Rate Fetching:** The service first identifies all unique currency codes (e.g., 150 codes) and then makes **concurrent** calls for those 150 rates, rather than making 200+ sequential network calls inside a loop.
3.  **Bulk Persistence:** Country data is saved to the database using `session.bulk_save_objects()`, requiring only **one** transaction commit for all hundreds of records.

### Ports and Adapters

The project structure cleanly separates business logic from technical implementation details:

  * **Domain:** Contains Entities (`Country`) and Ports (Abstract repositories like `AbstractCountryPersistence`).
  * **Application:** Contains Use Cases/Services (`RefreshCountriesService`) that orchestrate the flow.
  * **Infrastructure:** Contains Adapters (e.g., `SQLCountryRepository`, `RestCountriesAdapter`, `PillowImageAdapter`) which implement the Ports using concrete tools like SQLAlchemy, `httpx`, or Pillow.

This design ensures the core business logic is testable and independent of the framework or database choice.
