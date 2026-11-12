export type UserRole = 'platform_admin' | 'org_admin' | 'maintainer' | 'technician' | 'viewer' | 'demo_user'

export interface User {
  id: string
  email: string
  name: string
  status: 'pending' | 'active' | 'rejected' | 'suspended'
  is_superuser: boolean
  roles: string[]
  assigned_roles?: Array<{
    role: {
      key: string
      name: string
    }
  }>
  organization_id?: string | null
}

export interface Organization {
  id: string
  name: string
  slug: string
  status: 'active' | 'suspended' | 'archived'
}

export interface Equipment {
  id: string
  organization_id: string
  equipment_type_id: string
  name: string
  asset_tag: string
  manufacturer?: string | null
  model_number?: string | null
  serial_number?: string | null
  location_label?: string | null
  status: 'operational' | 'maintenance' | 'out_of_service' | 'archived'
  specification?: Record<string, any>
  components_count?: number
  sensors_count?: number
  created_at: string
}

export interface Component {
  id: string
  equipment_id: string
  component_key: string
  name: string
  component_type: string
  description?: string | null
  status: string
}

export interface Sensor {
  id: string
  equipment_id: string
  component_id?: string | null
  sensor_key: string
  measurement_type: string
  unit: string
  status: string
}

export interface SensorReading {
  id: string
  sensor_id: string
  equipment_id: string
  timestamp: string
  value: number
  unit: string
  quality_status: 'valid' | 'partial' | 'invalid'
}

export interface EquipmentHealthStatus {
  equipment_id: string
  name: string
  asset_tag: string
  status: string
  is_stale: boolean
  latest_reading?: {
    timestamp: string
    temperature_c?: number | null
    vibration_value?: number | null
    speed_rpm?: number | null
  } | null
  open_alerts_count: number
}

export interface MonitoringRule {
  id: string
  organization_id: string
  equipment_type_id?: string | null
  name: string
  measurement_type: string
  operator: 'gt' | 'gte' | 'lt' | 'lte' | 'eq' | 'neq'
  threshold: number
  unit: string
  duration_seconds: number
  severity: 'low' | 'medium' | 'high' | 'critical'
  is_active: boolean
}

export interface Alert {
  id: string
  organization_id: string
  equipment_id: string
  equipment_name?: string
  equipment_asset_tag?: string
  anomaly_event_id?: string | null
  alert_type: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  status: 'open' | 'acknowledged' | 'resolved' | 'dismissed'
  title: string
  description?: string | null
  acknowledged_by?: string | null
  acknowledged_at?: string | null
  resolved_by?: string | null
  resolved_at?: string | null
  resolution_note?: string | null
  created_at: string
}

export interface DiagnosisEvidence {
  id: string
  evidence_type: 'rule' | 'prediction' | 'graph' | 'sensor' | 'manual'
  source_reference?: string | null
  weight: number
  details_json: Record<string, any>
  created_at: string
}

export interface Diagnosis {
  id: string
  organization_id: string
  equipment_id: string
  primary_fault_id?: string | null
  primary_fault_key?: string | null
  primary_fault_name?: string | null
  status: 'normal' | 'attention_required' | 'possible_fault' | 'insufficient_data' | 'under_review' | 'confirmed_by_reviewer' | 'dismissed'
  severity: 'low' | 'medium' | 'high' | 'critical'
  confidence_score: number
  summary: string
  diagnostic_policy_version: string
  generated_at: string
  reviewed_by?: string | null
  reviewed_at?: string | null
  review_note?: string | null
  review_status: 'pending' | 'confirmed_by_reviewer' | 'dismissed' | 'rejected'
  evidence_items: DiagnosisEvidence[]
}

export interface StoredFile {
  id: string
  organization_id: string
  uploaded_by: string
  maintenance_record_id?: string | null
  original_filename: string
  media_type: string
  size_bytes: number
  checksum: string
  purpose: string
  created_at: string
}

export interface MaintenanceRecord {
  id: string
  organization_id: string
  equipment_id: string
  equipment_name?: string | null
  equipment_asset_tag?: string | null
  diagnosis_id?: string | null
  related_alert_id?: string | null
  created_by: string
  assigned_to?: string | null
  title: string
  description?: string | null
  maintenance_type: 'corrective' | 'preventive' | 'condition_based' | 'emergency'
  status: 'scheduled' | 'in_progress' | 'completed' | 'cancelled'
  priority: 'low' | 'medium' | 'high' | 'critical'
  scheduled_at?: string | null
  started_at?: string | null
  completed_at?: string | null
  inspection_timestamp?: string | null
  symptoms?: string | null
  diagnostic_findings?: string | null
  work_performed?: string | null
  parts_replaced_json?: any[] | null
  outcome: 'resolved' | 'not_resolved' | 'inconclusive' | 'pending_verification'
  verification_status: 'pending' | 'verified' | 'rejected'
  verified_by?: string | null
  verified_at?: string | null
  verification_note?: string | null
  notes?: string | null
  created_at: string
  updated_at: string
  attachments: StoredFile[]
}

export interface AuditLog {
  id: string
  organization_id?: string | null
  actor_user_id?: string | null
  actor_name?: string | null
  action: string
  resource_type?: string | null
  resource_id?: string | null
  created_at: string
  metadata?: Record<string, any>
}

export interface RegistrationRequest {
  id: string
  name: string
  email: string
  organization_name?: string | null
  status: 'pending' | 'approved' | 'rejected'
  created_at: string
}

