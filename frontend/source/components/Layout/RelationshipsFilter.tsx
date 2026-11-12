/** @jsxImportSource react */
/**
 * Structural relationships shown as checkboxes above the roles tree.
 * Selection shares the role id set used by the network request.
 * The heading reset restores the default relationships for the open entity
 * and reloads the network the same way a checkbox change does.
 */
import React, { useEffect, useState } from "react";
import { musigreeManager } from "../../core/singletons";
import {
    RANDOM_ARTIST_FILTER_RESET_EVENT,
    RANDOM_ARTIST_RELATIONSHIP_NAMES,
    defaultRelationshipNames,
    rememberRelationships,
    replaceManagedRoleSelection,
} from "../../roles";
import type { TreeNode } from "../../roles";

interface RelationshipsFilterProps {
    relationships: TreeNode[];
    onSelectionChange: () => void;
}

export const RelationshipsFilter: React.FC<RelationshipsFilterProps> = ({
    relationships,
    onSelectionChange,
}): React.ReactElement => {
    const [selectedIds, setSelectedIds] = useState<Set<string | number>>(
        () => new Set(),
    );

    useEffect(() => {
        const initial = new Set(
            relationships
                .filter((role) => role.state?.selected)
                .map((role) => role.id),
        );
        setSelectedIds(initial);
        rememberRelationships(relationships);
        replaceManagedRoleSelection(
            relationships.map((role) => role.id),
            Array.from(initial),
        );
    }, [relationships]);

    useEffect(() => {
        const artistNames = new Set<string>(RANDOM_ARTIST_RELATIONSHIP_NAMES);
        const applyRandomArtistRelationships = (): void => {
            setSelectedIds(
                new Set(
                    relationships
                        .filter((role) => artistNames.has(role.text))
                        .map((role) => role.id),
                ),
            );
        };
        window.addEventListener(
            RANDOM_ARTIST_FILTER_RESET_EVENT,
            applyRandomArtistRelationships,
        );
        return (): void => {
            window.removeEventListener(
                RANDOM_ARTIST_FILTER_RESET_EVENT,
                applyRandomArtistRelationships,
            );
        };
    }, [relationships]);

    const handleToggle = (id: string | number, checked: boolean): void => {
        const next = new Set(selectedIds);
        if (checked) {
            next.add(id);
        } else {
            next.delete(id);
        }
        setSelectedIds(next);
        replaceManagedRoleSelection(
            relationships.map((role) => role.id),
            Array.from(next),
        );
        onSelectionChange();
    };

    /** Restores the default relationships for the entity on screen. */
    const handleResetRelationships = (): void => {
        const defaults = new Set<string>(
            defaultRelationshipNames(
                musigreeManager.selectedNodeKey,
                window.location.pathname,
            ),
        );
        const next = new Set(
            relationships
                .filter((role) => defaults.has(role.text))
                .map((role) => role.id),
        );
        setSelectedIds(next);
        replaceManagedRoleSelection(
            relationships.map((role) => role.id),
            Array.from(next),
        );
        onSelectionChange();
    };

    const renderOption = (role: TreeNode): React.ReactElement => (
        <label className="relationships-option" key={role.id}>
            <input
                type="checkbox"
                checked={selectedIds.has(role.id)}
                onChange={(event) => {
                    handleToggle(role.id, event.target.checked);
                }}
            />
            <span>{role.text}</span>
        </label>
    );

    return (
        <>
            <div className="filter-heading h6 mt-3 mb-1">
                Relationships
                <button
                    type="button"
                    className="filter-reset"
                    aria-label="Reset relationships"
                    onClick={handleResetRelationships}
                >
                    <i
                        className="bi bi-arrow-counterclockwise"
                        aria-hidden="true"
                    ></i>
                </button>
            </div>
            <div
                className="relationships-filter"
                role="group"
                aria-label="Relationships"
            >
                {relationships.map(renderOption)}
            </div>
        </>
    );
};

export default RelationshipsFilter;
