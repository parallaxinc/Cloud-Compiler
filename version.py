

version = "1.3.8"

# Change Log
# 1.3.8
# Correct issue where writing source and header files to local
# storage was failing if the input bytestream contained an
# extended character, such as a degree symbol.
#
# 1.3.7
# Correct an issue where json was asked to encode a byte array,
# which it cannot do natively.
#
# 1.3.6
# Add missing s3_init binary.
# Change 'ping' endpoint logging to debug to reduce log noise.

# (1.3.5)
# Package updates
#
# Flask==1.0.2 => Flask==1.1.1
# Flask-Cors==3.0.7 => Flask-Cors==3.0.8
# sentry-sdk==0.7.6 => sentry-sdk==0.11.2
# Werkzeug==0.15.2 => Werkzeug==0.15.5
#
# -----------------------------------------------
