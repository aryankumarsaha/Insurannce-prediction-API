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

# 4. Create the startup script to run both servers simultaneously
# We use '0.0.0.0' so the services are accessible outside the container
RUN echo "#!/bin/sh\n\
uvicorn app:app --host 0.0.0.0 --port 8000 &\n\
streamlit run frontend.py --server.port 8501 --server.address 0.0.0.0\n\
wait" > start.sh

# Make the script executable
RUN chmod +x start.sh

# Set environment for Streamlit
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_ENABLEXSRF=false
ENV PYTHONUNBUFFERED=1

# Run the startup script
CMD ["./start.sh"]