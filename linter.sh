#!/bin/bash

# argument validation and usage help
usage()
{
cat << EOF
usage: $0 options

Lint a Postman collection or workspace using spectral rules:

OPTIONS:
    -c <collection ID> (see https://support.postman.com/hc/en-us/articles/5063785095319-How-to-find-the-ID-of-an-element-in-Postman)
    -w <workspace ID> (see https://support.postman.com/hc/en-us/articles/5063785095319-How-to-find-the-ID-of-an-element-in-Postman)
    -k <Postman API key> (defaults to the environment variable POSTMAN_API_KEY)
    -r <path to rules file> (defaults to rules.yaml for collections, workspacerules.yaml for workspaces)

Requirements: curl, spectral, jq
More information can be found here: https://github.com/postmanlabs/postman-collection-spectral-linter
EOF
}

if [ $# -eq 0 ]; then
    usage
    exit 1
fi

API_KEY=$POSTMAN_API_KEY
COLLECTION_RULES_PATH=rules.yaml
WORKSPACE_RULES_PATH=workspacerules.yaml

OPTSTRING=":c:w:k:r:"

while getopts ${OPTSTRING} opt; do
  case ${opt} in
    c)
        COLLECTION_UID=${OPTARG}
        ;;
    w)
        WORKSPACE_UID=${OPTARG}
        ;;
    k)
        API_KEY=${OPTARG}
        ;;
    r)
        if [ ! -z "$COLLECTION_UID" ]; then
            COLLECTION_RULES_PATH=${OPTARG}
        elif [ ! -z "$WORKSPACE_UID" ]; then
            WORKSPACE_RULES_PATH=${OPTARG}
        fi
        ;;
    :)
        echo "Option -${OPTARG} requires an argument."
        exit 1
        ;;
    ?)
        echo "Invalid option: -${OPTARG}."
        exit 1
        ;;
  esac
done

if [ -z "$API_KEY" ]; then
    usage
    exit 1
fi

if [ ! -z "$COLLECTION_UID" ]; then
    # Perform a curl request against the Postman API for a collection. Save the request body in a file called collection.json
    curl -s -H "x-api-key: $API_KEY" https://api.postman.com/collections/$COLLECTION_UID | jq . > _collection.json

    # Lint the collection using spectral. Save the result in a JSON file
    spectral lint _collection.json --ruleset $COLLECTION_RULES_PATH -f json --quiet > _result.json
elif [ ! -z "$WORKSPACE_UID" ]; then
    # Perform a curl request against the Postman API for a workspace. Save the request body in a file called workspace.json
    curl -s -H "x-api-key: $API_KEY" https://api.postman.com/workspaces/$WORKSPACE_UID | jq . > _workspace.json

    # Lint the workspace using spectral. Save the result in a JSON file
    spectral lint _workspace.json --ruleset $WORKSPACE_RULES_PATH -f json --quiet > _result.json
else
    echo "You must specify either a collection ID (-c) or a workspace ID (-w)."
    exit 1
fi
if [ -f _result.json ]; then
    echo "Linting completed. Processing results..."

    # Use jq to check if there are any errors (severity 0 or higher)
    jq '.[] | select(.severity >= 0)' -e _result.json >/dev/null

    if [ $? -eq 0 ]; then
        # Format the output in a human-readable way
        jq -r '
            .[] | 
            select(.severity >= 0) | 
            "Error: \(.message)\nCode: \(.code)\nPath: \(.path | join("."))\nSource: \(.source)\nLocation: Line \(.range.start.line), Character \(.range.start.character)\n"
        ' _result.json > _formatted_results.txt

        echo "Errors found:"
        cat _formatted_results.txt
        exit 1
    else
        echo "No errors found."
    fi
else
    echo "No results file found."
    exit 1
fi