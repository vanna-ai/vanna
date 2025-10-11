"""
Component state management and update protocol for rich components.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Union

from pydantic import BaseModel, Field

from ..components.rich import ComponentLifecycle, RichComponent


class UpdateOperation(str, Enum):
    """Types of component update operations."""

    CREATE = "create"
    UPDATE = "update"
    REPLACE = "replace"
    REMOVE = "remove"
    REORDER = "reorder"
    BULK_UPDATE = "bulk_update"


class Position(BaseModel):
    """Position specification for component placement."""

    index: Optional[int] = None
    anchor_id: Optional[str] = None
    relation: str = "after"  # "before", "after", "inside", "replace"


class ComponentUpdate(BaseModel):
    """Represents a change to the component tree."""

    operation: UpdateOperation
    target_id: str  # Component being affected
    component: Optional[RichComponent] = None  # New/updated component data
    updates: Optional[Dict[str, Any]] = None  # Partial updates for UPDATE operation
    position: Optional[Position] = None  # For positioning operations
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    batch_id: Optional[str] = None  # For grouping related updates

    def serialize_for_frontend(self) -> Dict[str, Any]:
        """Return update payload with nested components normalized."""
        payload = self.model_dump()

        # Normalise enum values for the frontend contract.
        payload["operation"] = self.operation.value

        if self.component:
            payload["component"] = self.component.serialize_for_frontend()

        return payload


class ComponentNode(BaseModel):
    """Node in the component tree."""

    component: RichComponent
    children: List["ComponentNode"] = Field(default_factory=list)
    parent_id: Optional[str] = None

    def find_child(self, component_id: str) -> Optional["ComponentNode"]:
        """Find a child node by component ID."""
        for child in self.children:
            if child.component.id == component_id:
                return child
            found = child.find_child(component_id)
            if found:
                return found
        return None

    def remove_child(self, component_id: str) -> bool:
        """Remove a child component by ID."""
        for i, child in enumerate(self.children):
            if child.component.id == component_id:
                self.children.pop(i)
                return True
            if child.remove_child(component_id):
                return True
        return False

    def get_all_ids(self) -> Set[str]:
        """Get all component IDs in this subtree."""
        ids = {self.component.id}
        for child in self.children:
            ids.update(child.get_all_ids())
        return ids


class ComponentTree(BaseModel):
    """Hierarchical structure for managing component layout."""

    root: Optional[ComponentNode] = None
    flat_index: Dict[str, ComponentNode] = Field(default_factory=dict)

    def add_component(self, component: RichComponent, position: Optional[Position] = None) -> ComponentUpdate:
        """Add a component to the tree."""
        node = ComponentNode(component=component)
        self.flat_index[component.id] = node

        if self.root is None:
            self.root = node
        else:
            parent_node = self._find_parent(position)
            if parent_node is not None:
                node.parent_id = parent_node.component.id
                parent_node.children.append(node)

        return ComponentUpdate(
            operation=UpdateOperation.CREATE,
            target_id=component.id,
            component=component,
            position=position
        )

    def update_component(self, component_id: str, updates: Dict[str, Any]) -> Optional[ComponentUpdate]:
        """Update a component's properties."""
        node = self.flat_index.get(component_id)
        if not node:
            return None

        # Create updated component
        component_data = node.component.model_dump()
        component_data.update(updates)
        component_data["lifecycle"] = ComponentLifecycle.UPDATE
        component_data["timestamp"] = datetime.utcnow().isoformat()

        updated_component = node.component.__class__(**component_data)
        node.component = updated_component

        return ComponentUpdate(
            operation=UpdateOperation.UPDATE,
            target_id=component_id,
            component=updated_component,
            updates=updates
        )

    def replace_component(self, old_id: str, new_component: RichComponent) -> Optional[ComponentUpdate]:
        """Replace one component with another."""
        old_node = self.flat_index.get(old_id)
        if not old_node:
            return None

        # Update the component in place
        old_node.component = new_component

        # Update index
        del self.flat_index[old_id]
        self.flat_index[new_component.id] = old_node

        return ComponentUpdate(
            operation=UpdateOperation.REPLACE,
            target_id=old_id,
            component=new_component
        )

    def remove_component(self, component_id: str) -> Optional[ComponentUpdate]:
        """Remove a component and its children."""
        node = self.flat_index.get(component_id)
        if not node:
            return None

        # Remove from parent
        if self.root and self.root.component.id == component_id:
            self.root = None
        else:
            if self.root:
                self.root.remove_child(component_id)

        # Remove from flat index (including all children)
        removed_ids = node.get_all_ids()
        for removed_id in removed_ids:
            self.flat_index.pop(removed_id, None)

        return ComponentUpdate(
            operation=UpdateOperation.REMOVE,
            target_id=component_id
        )

    def get_component(self, component_id: str) -> Optional[RichComponent]:
        """Get a component by ID."""
        node = self.flat_index.get(component_id)
        return node.component if node else None

    def _find_parent(self, position: Optional[Position]) -> Optional[ComponentNode]:
        """Find the parent node for a new component."""
        if not position or not position.anchor_id:
            return self.root

        anchor_node = self.flat_index.get(position.anchor_id)
        if not anchor_node:
            return self.root

        if position.relation == "inside":
            return anchor_node
        elif position.relation in ["before", "after", "replace"]:
            # Find the parent of the anchor
            if anchor_node.parent_id:
                parent_node = self.flat_index.get(anchor_node.parent_id)
                return parent_node if parent_node else self.root
            else:
                return self.root
        else:
            return self.root


class ComponentManager:
    """Manages component lifecycle and state updates."""

    def __init__(self) -> None:
        self.components: Dict[str, RichComponent] = {}
        self.component_tree = ComponentTree()
        self.update_history: List[ComponentUpdate] = []
        self.active_batch: Optional[str] = None

    def emit(self, component: RichComponent) -> Optional[ComponentUpdate]:
        """Emit a component with smart lifecycle management."""
        if component.id in self.components:
            # Existing component - determine if this is an update or replace
            existing = self.components[component.id]

            if component.lifecycle == ComponentLifecycle.UPDATE:
                # Extract changes
                old_data = existing.model_dump()
                new_data = component.model_dump()
                updates = {k: v for k, v in new_data.items() if old_data.get(k) != v}

                update = self.component_tree.update_component(component.id, updates)
            else:
                # Replace
                update = self.component_tree.replace_component(component.id, component)
        else:
            # New component - always append
            update = self.component_tree.add_component(component, None)

        if update:
            self.components[component.id] = component
            self.update_history.append(update)

            if self.active_batch:
                update.batch_id = self.active_batch

        return update

    def update_component(self, component_id: str, **updates: Any) -> Optional[ComponentUpdate]:
        """Update specific fields of an existing component."""
        update = self.component_tree.update_component(component_id, updates)
        if update and update.component:
            self.components[component_id] = update.component
            self.update_history.append(update)

            if self.active_batch:
                update.batch_id = self.active_batch

        return update

    def replace_component(self, old_id: str, new_component: RichComponent) -> Optional[ComponentUpdate]:
        """Replace one component with another."""
        update = self.component_tree.replace_component(old_id, new_component)
        if update:
            self.components.pop(old_id, None)
            self.components[new_component.id] = new_component
            self.update_history.append(update)

            if self.active_batch:
                update.batch_id = self.active_batch

        return update

    def remove_component(self, component_id: str) -> Optional[ComponentUpdate]:
        """Remove a component and handle cleanup."""
        update = self.component_tree.remove_component(component_id)
        if update:
            self.components.pop(component_id, None)
            self.update_history.append(update)

            if self.active_batch:
                update.batch_id = self.active_batch

        return update

    def get_component(self, component_id: str) -> Optional[RichComponent]:
        """Get a component by ID."""
        return self.components.get(component_id)

    def get_all_components(self) -> List[RichComponent]:
        """Get all components in the manager."""
        return list(self.components.values())

    def start_batch(self) -> str:
        """Start a batch of related updates."""
        self.active_batch = str(uuid.uuid4())
        return self.active_batch

    def end_batch(self) -> Optional[str]:
        """End the current batch."""
        batch_id = self.active_batch
        self.active_batch = None
        return batch_id

    def get_updates_since(self, timestamp: Optional[str] = None) -> List[ComponentUpdate]:
        """Get all updates since a given timestamp."""
        if not timestamp:
            return self.update_history.copy()

        try:
            cutoff = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            return [
                update for update in self.update_history
                if datetime.fromisoformat(update.timestamp.replace('Z', '+00:00')) > cutoff
            ]
        except ValueError:
            return self.update_history.copy()

    def clear_history(self) -> None:
        """Clear the update history."""
        self.update_history.clear()

