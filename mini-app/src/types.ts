export type Role = 'ADMIN' | 'CUSTOMER'
export type ItemStatus = 'TO_BUY'|'ORDERED'|'PURCHASED_OFFLINE'|'ON_THE_WAY_TO_US'|'READY_FOR_PICKUP'|'RECEIVED'|'ASSIGNED_TO_SHIPMENT'|'SHIPPED'|'DELIVERED'|'CANCELLED'|'RETURN_IN_PROGRESS'|'RETURNED'
export interface AuthMe { app_user_id: string; role: Role; customer_id: string | null }
export interface Dashboard { to_buy: number; on_the_way: number; received: number; assigned_to_shipment: number }
export interface Item { id:string; customer_id:string; product_url:string; size:string|null; color:string|null; quantity:number; customer_note:string|null; status:ItemStatus; listed_price:string|null; listed_currency:string|null; created_at:string }
export interface Customer { id:string; display_name:string; phone:string|null; collection_status:string }
export interface CustomerProfile { display_name:string; phone:string|null; country_code:string|null; postal_code:string|null; region:string|null; city:string|null; address_line1:string|null; address_line2:string|null; complete:boolean }
export interface PaymentEvidence { id:string; item_id:string; note:string|null; original_filename:string|null; mime_type:string|null; has_image:boolean; created_at:string }
