import type { RoleCode } from '../lib/api/client'

export const authenticatedHomePath = '/homepage'

export const roleWorkspacePaths: Record<RoleCode, string> = {
  individual: '/personal',
  enterprise: '/enterprise',
  government: '/government',
  admin: authenticatedHomePath,
}

export function roleWorkspacePath(role: RoleCode): string {
  return roleWorkspacePaths[role]
}
