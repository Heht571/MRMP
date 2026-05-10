export interface User {
  id: string
  username: string
  email?: string
  full_name?: string
  is_active?: boolean
}

export interface LoginForm {
  username: string
  password: string
}

export interface ModelAttribute {
  id: string
  name: string
  label: string
  type: string
  is_required: boolean
  is_unique: boolean
  is_list: boolean
  enum_values?: Array<{ label: string; value: string }>
  default_value?: string
  description?: string
  is_computed?: boolean
  compute_expr?: string
}

export interface Model {
  id: string
  name: string
  code: string
  description?: string
  category: string
  icon?: string
  color?: string
  is_active: boolean
  is_root_model?: boolean
  attributes?: ModelAttribute[]
  created_at?: string
  updated_at?: string
}

export interface Instance {
  id: string
  name: string
  code?: string
  model_id: string
  model_name?: string
  description?: string
  status?: string
  data: Record<string, unknown>
  created_at?: string
  updated_at?: string
  created_by?: string
}

export interface GlobalAttribute {
  id: string
  name: string
  label: string
  description?: string
  type: string
  is_choice: boolean
  is_list: boolean
  is_unique: boolean
  is_indexed: boolean
  is_sortable: boolean
  is_reference: boolean
  is_computed: boolean
  default_value?: string
  enum_values?: Array<{ label: string; value: string }>
  validation_regex?: string
  reference_model?: Model
}

export interface RelationDefinition {
  id: string
  code: string
  relation_label: string
  source_model_id: string
  target_model_id: string
  relation_type: string
  description?: string
}

export interface InstanceRelation {
  id: string
  source_instance_id: string
  target_instance_id: string
  relation_definition_id: string
  relation_label?: string
}

export interface PageResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

export interface PaginatedQuery {
  page?: number
  page_size?: number
  model_id?: string
  keyword?: string
  filters?: string
}

export interface ImportResult {
  total: number
  createCount: number
  updateCount: number
  errorCount: number
  errors: Array<{ row: number; message: string }>
}

export interface FieldMapping {
  systemField: string
  systemLabel: string
  mappedColumn: string | null
  required: boolean
}

export interface PreviewData {
  total: number
  createCount: number
  updateCount: number
  errorCount: number
  errors: Array<{ row: number; message: string }>
  data: unknown[]
  columns: string[]
  fileColumns: string[]
  sampleData: unknown[] | null
}