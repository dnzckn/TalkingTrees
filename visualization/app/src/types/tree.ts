/** Tree definition types matching the Python Pydantic models. */

export interface BlackboardPort {
  type: string;
  required: boolean;
  description?: string;
  default?: unknown;
}

export interface MacroMetadata {
  name: string;
  description?: string;
  collapsed: boolean;
  color?: string;
}

export interface TreeNodeDefinition {
  node_type: string;
  node_id: string;
  name: string;
  config: Record<string, unknown>;
  description?: string;
  children: TreeNodeDefinition[];
  $ref?: string;
  tree_id?: string;
  tree_file?: string;
  parameter_map?: Record<string, string>;
  blackboard_input?: Record<string, BlackboardPort>;
  blackboard_output?: Record<string, BlackboardPort>;
  macro?: MacroMetadata;
}

export interface TreeMetadata {
  name: string;
  version: string;
  author?: string;
  created_at?: string;
  modified_at?: string;
  description?: string;
  tags: string[];
  changelog?: string;
  status: 'draft' | 'active' | 'deprecated' | 'archived';
}

export interface TreeDefinition {
  $schema: string;
  tree_id: string;
  metadata: TreeMetadata;
  root: TreeNodeDefinition;
  subtrees: Record<string, TreeNodeDefinition>;
  dependencies?: {
    behaviors: string[];
    subtrees: string[];
    external: string[];
  };
}

/** Internal canvas node representation. */
export interface CanvasNode {
  id: string;
  nodeType: string;
  name: string;
  config: Record<string, unknown>;
  description?: string;
  parentId: string | null;
  childIds: string[];
  x: number;
  y: number;
  width: number;
  height: number;
  collapsed: boolean;
  macro?: MacroMetadata;
  blackboardInput?: Record<string, BlackboardPort>;
  blackboardOutput?: Record<string, BlackboardPort>;
  treeFile?: string;
  treeId?: string;
  ref?: string;
  /** Runtime status during simulation */
  status?: 'SUCCESS' | 'FAILURE' | 'RUNNING' | 'INVALID';
}

export type NodeCategory = 'composite' | 'decorator' | 'action' | 'condition' | 'custom';
