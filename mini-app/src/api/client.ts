import type { AuthMe, Customer, Dashboard, Item } from '../types'
const baseUrl = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1'
export class ApiError extends Error { constructor(public status:number, message:string) { super(message) } }
async function request<T>(path:string, initData:string): Promise<T> {
  const response = await fetch(`${baseUrl}${path}`, {headers:{'X-Telegram-Init-Data':initData}})
  if (!response.ok) {
    let message = `Request failed (${response.status})`
    try { const body = await response.json(); if (typeof body.detail === 'string') message = body.detail } catch { /* not JSON */ }
    throw new ApiError(response.status, message)
  }
  return response.json() as Promise<T>
}
export const api = {
  me:(data:string)=>request<AuthMe>('/auth/me',data), dashboard:(data:string)=>request<Dashboard>('/dashboard',data),
  items:(data:string)=>request<Item[]>('/items',data), customers:(data:string)=>request<Customer[]>('/admin/customers',data),
  warehouse:(data:string)=>request<Item[]>('/admin/warehouse',data),
}
