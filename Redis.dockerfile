# Use the official Redis image as the base.
FROM redis:7.0

# Copy your custom Redis configuration file.
# If you don't need a custom configuration, you can use the image as-is.
COPY redis.conf /usr/local/etc/redis/redis.conf

# Expose Redis default port.
EXPOSE 6379

# Start Redis using the custom configuration file.
CMD ["redis-server", "/usr/local/etc/redis/redis.conf"]
