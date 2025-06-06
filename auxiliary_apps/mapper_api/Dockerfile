# Use a Miniconda base image
FROM continuumio/miniconda3

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV ENV_NAME=biobert

# Create a Conda environment and install dependencies
COPY environment.yml /
RUN conda update -n base -c defaults conda && \
    conda env create -f /environment.yml && \
    conda clean --all --yes

# Activate the environment
SHELL ["conda", "run", "-n", "biobert", "/bin/bash", "-c"]

# Copy your project
COPY . /app/
WORKDIR /app

# Expose the port
EXPOSE 5000

# Run the app within the environment
CMD ["conda", "run", "-n", "biobert", "python", "app.py"]
