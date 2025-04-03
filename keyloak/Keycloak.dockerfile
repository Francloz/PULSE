FROM quay.io/keycloak/keycloak:latest

# Set the admin credentials (adjust these for your environment)
ENV KC_BOOTSTRAP_ADMIN_USERNAME=admin
ENV KC_BOOTSTRAP_ADMIN_PASSWORD=admin

# Expose the default HTTP port
EXPOSE 8080

# Start Keycloak in development mode
CMD ["start-dev"]
