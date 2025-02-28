#!/bin/bash

echo "Pulling environment secrets..."

function env_secret_debug() {
    if [ ! -z "$ENV_SECRETS_DEBUG" ]; then
        echo -e "\033[1m$@\033[0m"
    fi
}

# usage: env_secret_expand VAR
# XY_Z__FILE=/run/secrets/secret_file -> XY_Z=<contents of /run/secrets/secret_file>
env_secret_expand() {
    key="$1"
    eval value=\$$key
    if secret_name=$(expr match "$key" "\(.*\)__FILE$"); then
        if [ -f "$value" ]; then
            secret=$(cat "${value}")
            export "$secret_name"="$secret"
            env_secret_debug "Expanded variable: $secret_name=$secret"
        else
            env_secret_debug "Secret file does not exist! $value"
        fi
    else
        env_secret_debug "Environmental variable does not end with __FILE: $key=$value"
    fi
}

env_secrets_expand() {
    for env_var in $(printenv | cut -f1 -d"=")
    do
        env_secret_expand $env_var
    done

    if [ ! -z "$ENV_SECRETS_DEBUG" ]; then
        echo -e "\n\033[1mExpanded environment variables\033[0m"
        printenv
    fi
}

env_secrets_expand
exec "$@"
