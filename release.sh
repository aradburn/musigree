#!/usr/bin/env bash
#
# Release the project and bump version number in the process.

set -e

cd "$(dirname "$0")"

export PATH="$HOME/.local/bin:$PATH"

FORCE=false

usage() {
    echo "Usage: $0 [options] VERSION"
    echo
    echo "VERSION:"
    echo "  major: bump major version number"
    echo "  minor: bump minor version number"
    echo "  patch: bump patch version number"
    echo
    echo "Options:"
    echo "  -f, --force:  force release"
    echo "  -h, --help:   show this help message"
    exit 1
}

# parse args
while [ "$#" -gt 0 ]; do
    case "$1" in
    -f | --force)
        FORCE=true
        shift
        ;;
    -h | --help)
        usage
        ;;
    *)
        break
        ;;
    esac
done

# check if version is specified
if [ "$#" -lt 1 ]; then
    usage
fi

if [ "$1" != "major" ] && [ "$1" != "minor" ] && [ "$1" != "patch" ]; then
    usage
fi

# check if git is clean and force is not enabled
if ! git diff-index --quiet HEAD -- && [ "$FORCE" = false ]; then
    echo "Error: git is not clean. Please commit all changes first."
    exit 1
fi

if ! command -v uv &> /dev/null; then
    echo "Error: uv is not installed. Please install uv from https://docs.astral.sh/uv/"
    exit 1
fi

echo "Would bump version:"
uv version --bump "$1" --dry-run

# prompt for confirmation
if [ "$FORCE" = false ]; then
    read -p "Do you want to release? [yY] " -n 1 -r
    echo
else
    REPLY="y"
fi
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then

    # Check frontend passes tests
    echo "Check frontend passes tests..."
    cd frontend
    npm run check-type
    npm run lint
    npm run test
    npm audit
    cd ..

    # Check backend passes tests
    echo "Check backend passes tests..."
    uv run pytest tests/unit \
        --log-disable=musigree.app.fastapi_api \
        --log-disable=musigree.app.fastapi_app \
        --log-disable=musigree.app.fastapi_assets \
        --log-disable=musigree.app.fastapi_dependencies \
        --log-disable=musigree.app.fastapi_security \
        --log-disable=musigree.app.fastapi_ui \
        --log-disable=musigree.exceptions \
        --log-disable=musigree.exceptions \
        --log-disable=musigree.library.cache.cache_manager \
        --log-disable=musigree.library.full_text_search.text_search_index \
        --log-disable=musigree.loader.create_entity_details_index \
        --log-disable=musigree.loader.offline_loader \
        --log-disable=musigree.loader.runtime_loader \
        --log-disable=musigree.logging_config \
        --log-disable=musigree.offline.data_access_layer.release_data_access \
        --log-disable=musigree.offline.data_access_layer.role_data_access \
        --log-disable=musigree.offline.database.offline_transaction \
        --log-disable=musigree.offline.loader.loader_base \
        --log-disable=musigree.offline.loader.loader_role \
        --log-disable=musigree.offline.loader.loader_target \
        --log-disable=musigree.offline.loader.loader_utils \
        --log-disable=musigree.offline.loader.worker_entity_pass_three \
        --log-disable=musigree.offline.loader.worker_entity_updater \
        --log-disable=musigree.offline.offline_database_manager \
        --log-disable=musigree.runtime.data_access_layer.relation_grapher \
        --log-disable=musigree.runtime.data_access_layer.runtime_entity_data_access \
        --log-disable=musigree.runtime.data_access_layer.runtime_entity_search \
        --log-disable=musigree.runtime.data_access_layer.runtime_role_data_access \
        --log-disable=musigree.runtime.runtime_database_manager \
        --log-disable=musigree.runtime.runtime_database.runtime_transaction \
        --log-disable=musigree.transfer.transfer_manager \
        --log-disable=musigree.transfer.transfer_task \
        --log-disable=musigree.utils \
        --disable-warnings --no-header --no-summary

    # replace version number
    uv version --bump "$1"

    new_version=$(uv version --short)

    # Update frontend to be same version as backend
    cd frontend
    npm version --no-git-tag-version "$new_version"
    echo "export const version = \"$new_version\";" > source/version.ts
    cd ..

    # commit changes
    git add pyproject.toml uv.lock frontend/package.json frontend/package-lock.json frontend/source/version.ts
    git commit -m "bump version to $new_version"
    # git tag -a "v$new_version" -m "v$new_version"

    # push changes
    # git push origin main
    # git push origin "v$new_version"
else
    echo "Aborted."
    exit 1
fi
