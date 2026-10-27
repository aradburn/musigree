/** @jsxImportSource react */
/**
 * Structural relationships shown as checkboxes above the roles tree.
 * Selection shares the role id set used by the network request.
 */
import React, { useEffect, useState } from "react";
import {
    RANDOM_ARTIST_FILTER_RESET_EVENT,
    RANDOM_ARTIST_RELATIONSHIP_NAMES,
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
        <div
            className="relationships-filter"
            role="group"
            aria-label="Relationships"
        >
            {relationships.map(renderOption)}
        </div>
    );
};

export default RelationshipsFilter;
