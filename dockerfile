# Use a slim Python image to save space
FROM python:3.10-slim

# Set working directory inside the container
WORKDIR /app

# 1. Install dependencies first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2. Copy ALL files from your current directory into the container
# This includes app.py, frontend.py, model.pkl, and the schema/config folders
COPY . .

# 3. Expose ports for both services
EXPOSE 8000
EXPOSE 8501

# Set environment for Streamlit
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_ENABLEXSRF=false
ENV PYTHONUNBUFFERED=1

# Run both services simultaneously
CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000} & streamlit run frontend.py --server.port ${STREAMLIT_PORT:-8501} --server.address 0.0.0.0 & wait"]