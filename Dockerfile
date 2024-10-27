FROM python


# Set working directory
WORKDIR /app

COPY . /app

# Install dependencies
RUN pip install -r requirements.txt

# Expose port 7000 for the Flask app
EXPOSE 7070

# Start the Flask app
CMD ["python", "app.py"]
