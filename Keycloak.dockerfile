# Use the official Keycloak image as the base image.
FROM quay.io/keycloak/keycloak:latest

# Copy your custom realm configuration into the container.
# This file will be imported automatically if you start Keycloak with the proper flag.
COPY realm.json /opt/keycloak/data/import/realm.json

# Set environment variables for the admin user.
ENV KEYCLOAK_ADMIN=admin \
    KEYCLOAK_ADMIN_PASSWORD=admin

# Expose the default Keycloak port (adjust if needed).
EXPOSE 8080

# Start Keycloak in development mode (or change to your desired startup mode).
CMD ["start-dev"]
